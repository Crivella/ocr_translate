###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
import logging
import queue
import threading
import time
from typing import Callable, Hashable, Iterable, Union

logger = logging.getLogger('ocr.worker')


class NotHandled():
    pass

class Message():
    NotHandled = NotHandled
    def __init__(
            self, id: Hashable, msg: dict, handler: Callable,
            batch_args: tuple = (), batch_kwargs: Iterable = ()
            ):
        """Message object to be used in WorkerMessageQueue.
        Params:
            id (Hashable): Message id. Used to identify messages with the same id.
            msg (dict): Message to be passed to the handler.
            handler (Callable): Handler function to be called with the message.
            batch_args (tuple, optional): Indexes of the args to be batched. Defaults to ().
            batch_kwargs (Iterable, optional): Keys of the kwargs to be batched. Defaults to ().
        """
        self.id = id
        self.msg = msg
        self.handler = handler
        self.batch_args = batch_args
        self.batch_kwargs = batch_kwargs
        self._response = NotHandled

    def resolve(self):
        """Resolve the message by calling the handler with the message.
        This operation is synchronous and will block the exection until the handler is done."""
        self._response = self.handler(*self.msg.get('args', ()), **self.msg.get('kwargs', {}))
        logger.debug(f'MSG Resolved {self.msg} -> {self._response}')

        # Make sure to dereference the message to avoid keeping raw images in memory
        # since i am gonna keep the message in the queue after it is resolved (for msg caching)
        del self.msg

    def batch_resolve(self, others: Iterable['Message']):
        """Resolve multiple messages with one call to the handler.
        The handler must be able to handle the specified batched args and kwargs, as either the expected type or a list of the expected type.
        The handler must return a list of the same length as the number of messages to be resolved, with the same order.
        """
        logger.debug(f'MSG Batch Resolving {self.msg} with {len(others)} other messages')
        # Check if these checks are necessary (maybe just let the handler fail)
        # Main problem would be running messages with different non batched args that produce worng results
        # But having all these checks might slow down the batching too much
        if any([_.handler != self.handler for _ in others]):
            raise ValueError('All messages must have the same handler')
        check = len(self.msg['args'])
        if any([len(_.msg['args']) != check for _ in others]):
            raise ValueError('All messages must have the same number of args')
        check = set(self.msg['kwargs'].keys())
        if any([set(_.msg['kwargs'].keys()) != check for _ in others]):
            raise ValueError('All messages must have the same kwargs')
        # Should also check that the non-batched args and kwargs are the same for all messages
        
        args = [[a] if i in self.batch_args else a for i, a in enumerate(self.msg['args'])]
        kwargs = {k:[v] if i in self.batch_kwargs else v for i, (k, v) in enumerate(self.msg['kwargs'].items())}

        for msg in others:
            for i in self.batch_args:
                args[i].append(msg.msg['args'][i])
            for k in self.batch_kwargs:
                kwargs[k].append(msg.msg['kwargs'][k])

        respones = self.handler(*args, **kwargs)
        for msg, r in zip([self, *others], respones):
            logger.debug(f'MSG Batch Resolved {msg.msg} -> {r}')
            msg._response = r

            # Make sure to dereference the message to avoid keeping raw images in memory
            # since i am gonna keep the message in the queue after it is resolved (for msg caching)
            del msg.msg

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
            if isinstance(msg, Message):
                msg.resolve()
            elif isinstance(msg, list):
                if len(msg) == 0:
                    continue
                if len(msg) == 1:
                    msg[0].resolve()
                else:
                    msg[0].batch_resolve(msg[1:])
            else:
                raise ValueError(f'Invalid message type: {type(msg)}')
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
            allow_batching: bool = False, 
            batch_timeout: float = 0.5, 
            batch_args: tuple = (), batch_kwargs: Iterable = (),
            **kwargs
            ):
        """
        Args:
            num_workers (int, optional): Number of workers to spawn. Defaults to 1.
            reuse_msg (bool, optional): Whether to reuse messages with the same id. Defaults to True.
            max_len (int, optional): Max number of messages in queue before starting to remove solved messages from cache.
                                     Defaults to 0 (no limit).
            allow_batching (bool, optional): Whether to allow batching of messages. Defaults to False.
                Batching is done by grouping messages with the same args, kwargs and handler (excluding the arguments to be batched).
            batch_timeout (float, optional): Timeout for batching. Defaults to 0.5.
            batch_args (tuple, optional): Indexes of the args to be batched. Defaults to ().
            batch_kwargs (Iterable, optional): Keys of the kwargs to be batched. Defaults to ().
        """
        super().__init__(*args, **kwargs)
        self.registered = {}
        self.batch_pools = {}
        self.msg_to_batch_pool = {}
        self.batch_resolve_flagged = []
        self.reuse_msg = reuse_msg
        self.max_len = max_len
        self.allow_batching = allow_batching
        self.batch_timeout = batch_timeout
        self.batch_args = batch_args
        self.batch_kwargs = batch_kwargs
        self.workers = [Worker(self) for _ in range(num_workers)]

    def put(self, id: Hashable, msg: dict, handler: Callable, batch_id: Hashable = None) -> Message:
        if self.reuse_msg and id in self.registered:
            logger.debug(f'Reusing message {id}')
            return self.registered[id]
        if self.max_len > 0 and self.qsize() > self.max_len:
            # TODO: Remove solved messages from cache
            #  Only 1by1 or all?
            raise NotImplementedError('Max len reached')
        
        res = Message(id, msg, handler, batch_args=self.batch_args, batch_kwargs=self.batch_kwargs)
        if self.allow_batching and batch_id is not None:
            self.msg_to_batch_pool[id] = batch_id
            ptr = self.batch_pools.setdefault(batch_id, [])
            ptr.append(res)

        self.registered[id] = res

        super().put(res)

        return res
    
    def get(self, *args, **kwargs) -> Union[Message, list[Message]]:
        msg = super().get(*args, **kwargs)
        while msg.id in self.batch_resolve_flagged:
            self.batch_resolve_flagged.remove(msg.id)
            msg = super().get(*args, **kwargs)

        if self.allow_batching and msg.id in self.msg_to_batch_pool:
            # Wait for more messages to come
            logger.debug(f'Batching message {msg.id}')
            time.sleep(self.batch_timeout)

            logger.debug(f'Batching message {msg.id} done')
            pool_id = self.msg_to_batch_pool[msg.id]
            logger.debug(f'Batching message {msg.id} pool id {pool_id}')
            pool = self.batch_pools.pop(pool_id)
            logger.debug(f'Batching message {msg.id} pool {pool}')
            for msg in pool:
                self.msg_to_batch_pool.pop(msg.id)
                self.batch_resolve_flagged.append(msg.id)
            if len(pool) > 1:
                return pool

        return msg

    def get_msg(self, msg_id: str):
        return self.registered.get(msg_id, None)
    
    def start_workers(self):
        for w in self.workers:
            w.start()

    def stop_workers(self):
        for w in self.workers:
            w.stop()
    

    