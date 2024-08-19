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
"""Messaging and worker+queue system for ocr_translate."""
import logging
import queue
import threading
import time
from typing import Callable, Hashable, Iterable, Union

logger = logging.getLogger('ocr.worker')


class NotHandled():
    """Dummy object to be used as default response of an unresolved message."""

class Message():
    """Message object to be used in WorkerMessageQueue. This class is used to send a message in the queue, but
    also allow the sending function to wait for the response of the message."""
    NotHandled = NotHandled
    def __init__(
            self, id_: Hashable, msg: dict, handler: Callable,
            batch_args: tuple = (), batch_kwargs: Iterable = ()
            ):
        """Message object to be used in WorkerMessageQueue.

        Args:
            id_ (Hashable): Message id. Used to identify messages with the same id.
            msg (dict): Message to be passed to the handler.
            handler (Callable): Handler function to be called with the message.
            batch_args (tuple, optional): Indexes of the args to be batched. Defaults to ().
            batch_kwargs (Iterable, optional): Keys of the kwargs to be batched. Defaults to ().
        """
        self.id_ = id_
        self.msg = msg
        self.handler = handler
        self.batch_args = batch_args
        self.batch_kwargs = batch_kwargs
        self._response = NotHandled

    def resolve(self):
        """Resolve the message by calling the handler with the message.
        This operation is synchronous and will block the exection until the handler is done."""
        try:
            self._response = self.handler(*self.msg.get('args', ()), **self.msg.get('kwargs', {}))
        except Exception as exc:
            logger.error(f'Error resolving message {self.msg}', exc_info=True)
            self._response = exc
            # Avoid killing the worker thread
            # raise
        else:
            logger.debug(f'MSG Resolved {self.msg} -> {self._response}')

        # Make sure to dereference the message to avoid keeping raw images in memory
        # since i am gonna keep the message in the queue after it is resolved (for msg caching)
        del self.msg

    def batch_resolve(self, others: Iterable['Message']):
        """Resolve multiple messages with one call to the handler.
        The handler must be able to handle the specified batched args and kwargs,
        as either the expected type or a list of the expected type.
        The handler must return a list of the same length as the number of messages to be resolved, with the same order.
        """
        logger.debug(f'MSG Batch Resolving {self.msg} with {len(others)} other messages')
        # Check if these checks are necessary (maybe just let the handler fail)
        # Main problem would be running messages with different non batched args that produce worng results
        # But having all these checks might slow down the batching too much
        if any(_.handler != self.handler for _ in others):
            raise ValueError('All messages must have the same handler')
        check = len(self.msg['args'])
        if any(len(_.msg['args']) != check for _ in others):
            raise ValueError('All messages must have the same number of args')
        check = set(self.msg['kwargs'].keys())
        if any(set(_.msg['kwargs'].keys()) != check for _ in others):
            raise ValueError('All messages must have the same kwargs')
        # Should also check that the non-batched args and kwargs are the same for all messages

        args = [[a] if i in self.batch_args else a for i, a in enumerate(self.msg['args'])]
        kwargs = {k:[v] if k in self.batch_kwargs else v for k, v in self.msg['kwargs'].items()}

        for msg in others:
            for i in self.batch_args:
                args[i].append(msg.msg['args'][i])
            for k in self.batch_kwargs:
                kwargs[k].append(msg.msg['kwargs'][k])

        respones = self.handler(*args, **kwargs)
        for msg, r in zip([self, *others], respones):
            logger.debug(f'MSG Batch Resolved {msg.msg} -> {r}')
            msg.set_response(r)

            # Make sure to dereference the message to avoid keeping raw images in memory
            # since i am gonna keep the message in the queue after it is resolved (for msg caching)
            del msg.msg

    @property
    def is_resolved(self) -> bool:
        """Whether the message has been resolved or not."""
        return self._response is not NotHandled

    def set_response(self, response):
        """Set the response of the message."""
        self._response = response

    def response(self, timeout: float = 0, poll: float = 0.2):
        """Get the response of the message.

        Args:
            timeout (float, optional): Timeout in seconds to wait for the message to be resolved.
                Defaults to 0 (no timeout).
            poll (float, optional): Polling interval in seconds. Defaults to 0.2.

        Raises:
            TimeoutError: If the message is not resolved after the timeout.

        Returns:
            Any: The response of the message (return value of the handler called on the msg content).
        """
        start = time.time()

        while not self.is_resolved:

            if time.time() - start > timeout > 0:
                raise TimeoutError('Message resolution timed out')
            time.sleep(poll)

        return self._response

    def __repr__(self):
        return f'Message({self.msg}), Handler: {self.handler.__name__}'

    def __str__(self):
        return f'Message({self.msg}), Handler: {self.handler.__name__}'

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Message):
            return False

        res = True
        res &= self.id_ == __value.id_
        res &= self.msg == __value.msg
        res &= self.handler == __value.handler
        return res

    def copy(self) -> 'Message':
        """Return a copy of the message. Used for tests."""
        return Message(
            self.id_, dict(self.msg), self.handler,
            batch_args=self.batch_args, batch_kwargs=self.batch_kwargs
            )

class MessageQueue(queue.SimpleQueue):
    """Message queue with worker threads to resolve messages. This class extends queue.SimpleQueue, by adding:
        - Message caching/reuse (When a new message with the same id is put in the queue, the old one is returned)
        - Message batching (Messages with the same batch_id are grouped together and resolved with one handler call)
    """
    def __init__(
            self,
            *args,
            reuse_msg: bool = True,
            # max_len: int = 0,
            allow_batching: bool = False,
            batch_timeout: float = 0.5,
            batch_args: tuple = (), batch_kwargs: Iterable = (),
            **kwargs
            ):
        """Create a new WorkerMessageQueue.

        Args:
            reuse_msg (bool, optional): Whether to reuse messages with the same id. Defaults to True.
            max_len (int, optional): Max number of messages in cache before starting to remove solved messages
                from cache. Defaults to 0 (no limit).
            allow_batching (bool, optional): Whether to allow batching of messages. Defaults to False.
            batch_timeout (float, optional): Timeout for batching. When get is called, wait `timeout` seconds for other
                incoming messages. Defaults to 0.5.
            batch_args (tuple, optional): Indexes of the args to be batched. Defaults to ().
            batch_kwargs (Iterable, optional): Keys of the kwargs to be batched. Defaults to ().
        """
        super().__init__(*args, **kwargs)
        self.registered = {}
        self.batch_pools = {}
        self.msg_to_batch_pool = {}
        self.batch_resolve_flagged = []
        self.reuse_msg = reuse_msg
        # self.max_len = max_len
        if allow_batching:
            if len(batch_args) == 0 and len(batch_kwargs) == 0:
                raise ValueError('At least one batch arg or kwarg must be specified with batching enabled.')
        self.allow_batching = allow_batching
        self.batch_timeout = batch_timeout
        self.batch_args = batch_args
        self.batch_kwargs = batch_kwargs

    def put(self, id_: Hashable, msg: dict, handler: Callable, batch_id: Hashable = None) -> Message:
        """Put a new message in the queue.

        Args:
            id_ (Hashable): Id of the message. Used to identify messages with the same id.
            msg (dict): Message to be passed to the handler.
            handler (Callable): Handler function to be called with the message.
            batch_id (Hashable, optional): Id of the batch to which the message belongs. Defaults to None.

        Raises:
            NotImplementedError: If the max_len is reached.

        Returns:
            Message: The message object.
        """
        if batch_id is not None and not self.allow_batching:
            raise ValueError('Batching is not allowed')

        if self.reuse_msg and id_ in self.registered:
            logger.debug(f'Reusing message {id_}')
            return self.registered[id_]
        # if self.max_len > 0 and self.qsize() > self.max_len:
        #     # Remove solved messages from cache
        #     # Only 1by1 or all?
        #     raise NotImplementedError('Max len reached')

        res = Message(id_, msg, handler, batch_args=self.batch_args, batch_kwargs=self.batch_kwargs)
        if self.allow_batching and batch_id is not None:
            self.msg_to_batch_pool[id_] = batch_id
            ptr = self.batch_pools.setdefault(batch_id, [])
            ptr.append(res)

        if self.reuse_msg:
            self.registered[id_] = res

        super().put(res)

        return res

    def get(self, *args, **kwargs) -> Union[Message, list[Message]]:
        """Get a message or list of messages from the queue.

        Returns:
            Union[Message, list[Message]]: A message or a list of messages, depending on whether batching is enabled.
        """
        msg = super().get(*args, **kwargs)
        while msg.id_ in self.batch_resolve_flagged:
            self.batch_resolve_flagged.remove(msg.id_)
            msg = super().get(*args, **kwargs)

        if self.allow_batching and msg.id_ in self.msg_to_batch_pool:
            # Wait for more messages to come
            logger.debug(f'Batching message {msg.id_}')
            time.sleep(self.batch_timeout)

            logger.debug(f'Batching message {msg.id_} done')
            pool_id = self.msg_to_batch_pool[msg.id_]
            logger.debug(f'Batching message {msg.id_} pool id {pool_id}')
            pool = self.batch_pools.pop(pool_id)
            logger.debug(f'Batching message {msg.id_} pool {pool}')
            for msg in pool:
                self.msg_to_batch_pool.pop(msg.id_)
                self.batch_resolve_flagged.append(msg.id_)
            return pool

        return msg

    def get_msg(self, msg_id: str):
        """Get a message from the cache. If the message is not in the cache, return None.

        Args:
            msg_id (str): Id of the message.

        Returns:
            _type_: The message object or None.
        """
        if not self.reuse_msg:
            raise ValueError('Message caching is disabled')

        return self.registered.get(msg_id, None)

class Worker():
    """Worker object to be used in WorkerMessageQueue."""
    def __init__(self, attached_queue: MessageQueue, poll_interval: float = .2):
        self.queue = attached_queue
        self.kill = False
        self.running = False
        self.thread = None
        self.poll_interval = poll_interval

    def _worker(self):
        """Worker function that consumes messages from the queue and resolves them."""
        self.running = True
        while not self.kill:
            try:
                msg = self.queue.get(timeout=self.poll_interval)
            except queue.Empty:
                continue
            logger.debug(f'Worker consuming {msg}')
            if isinstance(msg, list):
                if len(msg) == 1:
                    msg[0].resolve()
                else:
                    msg[0].batch_resolve(msg[1:])
            else:
                msg.resolve()

        self.running = False

    def start(self):
        """Start the worker thread."""
        self.kill = False # Allow restarting the worker
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the worker thread."""
        self.kill = True
        self.thread.join()

class WorkerMessageQueue():
    """Bundle together the queue and its workers."""
    def __init__(self, *args, num_workers: int = 1, **kwargs):
        """Create a new WorkerMessageQueue.

        Args:
            num_workers (int, optional): Number of workers to spawn. Defaults to 1.
        """
        self.msg_queue = MessageQueue(*args, **kwargs)
        self.workers = [Worker(self.msg_queue) for _ in range(num_workers)]

    def put(self, id_: Hashable, msg: dict, handler: Callable, batch_id: Hashable = None) -> Message:
        """Call the put method of the queue."""
        return self.msg_queue.put(id_, msg, handler, batch_id=batch_id)

    def get(self, *args, **kwargs) -> Union[Message, list[Message]]:
        """Call the get method of the queue."""
        return self.msg_queue.get(*args, **kwargs)

    def get_msg(self, msg_id: str):
        """Call the get_msg method of the queue."""
        return self.msg_queue.get_msg(msg_id)

    def start_workers(self):
        """Start all the worker threads registered to this queue."""
        for worker in self.workers:
            worker.start()

    def stop_workers(self):
        """Stop all the worker threads registered to this queue."""
        for worker in self.workers:
            worker.stop()
