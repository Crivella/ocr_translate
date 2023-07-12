import logging
import queue
import threading
import time
from typing import Callable

logger = logging.getLogger('ocr.worker')


class NotHandled():
    pass

class Message():
    NotHandled = NotHandled
    def __init__(self, id: str, msg: dict, handler: Callable):
        self.id = id
        self.msg = msg
        self.handler = handler
        self._response = NotHandled

    def resolve(self):
        self._response = self.handler(*self.msg.get('args', ()), **self.msg.get('kwargs', {}))
        logger.debug(f'MSG Resolved {self.msg} -> {self._response}')
        # Make sure to dereference the message to avoid keeping raw images in memory
        # since i am gonna keep the message in the queue after it is resolved (for msg caching)
        del self.msg

    @property
    def is_resolved(self):
        return self._response is not NotHandled
    
    def response(self, timeout: float = 0, poll: float = 0.2):
        start = time.time()

        while not self.is_resolved:
            if timeout > 0 and time.time() - start > timeout:
                raise TimeoutError('Message resolution timed out')
            time.sleep(poll)

        return self._response
    
    def __str__(self):
        return f'Message({self.msg}), Handler: {self.handler.__name__}'

class Worker():
    def __init__(self, q: queue.SimpleQueue[Message]):
        self.q = q
        self.kill = False
        self.running = False
        self.thread = None

    def _worker(self):
        self.running = True
        while not self.kill:
            try:
                msg = self.q.get(timeout=1)
            except queue.Empty:
                continue
            logger.debug(f'Worker consuming {msg}')
            msg.resolve()
        self.running = False

    def start(self):
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.kill = True
        self.thread.join()

class WorkerMessageQueue(queue.SimpleQueue):
    def __init__(
            self, 
            *args, 
            num_workers: int = 1, 
            reuse_msg: bool = True, 
            max_len: int = 0, 
            **kwargs
            ):
        """
        Args:
            num_workers (int, optional): Number of workers to spawn. Defaults to 1.
            reuse_msg (bool, optional): Whether to reuse messages with the same id. Defaults to True.
            max_len (int, optional): Max number of messages in queue before starting to remove solved messages from cache.
                                     Defaults to 0 (no limit).
        """
        super().__init__(*args, **kwargs)
        self.registered = {}
        self.reuse_msg = reuse_msg
        self.max_len = max_len
        self.workers = [Worker(self) for _ in range(num_workers)]

    def put(self, id: str, msg: dict, handler: Callable) -> Message:
        if self.reuse_msg and id in self.registered:
            logger.debug(f'Reusing message {id}')
            return self.registered[id]
        if self.max_len > 0 and self.qsize() > self.max_len:
            # TODO: Remove solved messages from cache
            #  Only 1by1 or all?
            raise NotImplementedError('Max len reached')
        msg = Message(id, msg, handler)
        self.registered[id] = msg
        super().put(msg)

        return msg

    def get_msg(self, msg_id: str):
        return self.registered.get(msg_id, None)
    
    def start_workers(self):
        for w in self.workers:
            w.start()

    def stop_workers(self):
        for w in self.workers:
            w.stop()
    

    