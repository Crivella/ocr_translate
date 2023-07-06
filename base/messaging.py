import queue
import threading
from typing import Callable


class NotHandled():
    pass

class Message():
    NotHandled = NotHandled
    def __init__(self, id: str, message: dict, handler: Callable):
        self.id = id
        self.message = message
        self.handler = handler
        self._response = NotHandled

    def resolve(self):
        self._response = self.handler(*self.message['args'], **self.message['kwargs'])
        # Make sure to dereference the message to avoid keeping raw images in memory
        # since i am gonna keep the message in the queue after it is resolved (for msg caching)
        del self.message

    @property
    def is_resolved(self):
        return self._response is not NotHandled
    
    @property
    def response(self):
        if self._response is NotHandled:
            raise ValueError('Message not resolved')
        
        return self._response
    
    def __str__(self):
        return f'Message({self.message}), Handler: {self.handler.__name__}'

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
            print(f'Worker consuming {msg}')
            msg.resolve()
        self.running = False

    def start(self):
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.kill = True
        self.thread.join()

class WorkerMessageQueue(queue.SimpleQueue):
    def __init__(self, *args, num_workers=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.registered = {}
        self.workers = [Worker(self) for _ in range(num_workers)]

    def put(self, msg: Message):
        self.registered[msg.id] = msg
        super().put(msg)

    def get_msg(self, msg_id: str):
        return self.registered.get(msg_id, None)
    
    def start_workers(self):
        for w in self.workers:
            w.start()

    def stop_workers(self):
        for w in self.workers:
            w.stop()
    

    