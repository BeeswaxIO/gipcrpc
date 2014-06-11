#!/usr/bin/python
# -*- coding: utf-8 -*-
import gipc
import logging
import gevent
from gevent.event import AsyncResult
from gevent.queue import Queue
from collections import deque
from contextlib import contextmanager


__all__ = ('child_service', 'IPCRPCServer', 'IPCRPCClient')


@contextmanager
def child_service(klass, concurrency=10, queue_size=None):
    with gipc.pipe(duplex=True) as (child_channel, parent_channel):
        service = klass(concurrency=concurrency, queue_size=queue_size)
        service_process = gipc.start_process(target=service, args=(child_channel,))

        client = IPCRPCClient(parent_channel)
        try:
            yield client
        finally:
            client.close()
            service_process.join()
    

class IPCRPCServer(object):
    def __init__(self, concurrency=10, queue_size=None):
        self._queue_size = queue_size
        self._concurrency = concurrency

    def init(self):
        pass

    def _start_processors(self):
        # you must call this method after fork()
        self._queue = Queue(self._queue_size)
        self._threads = []
        for i in range(self._concurrency):
            thread = gevent.spawn(self._process_thread)
            self._threads.append(thread)

    def _process_thread(self):
        for req in self._queue:
            msg_id, method, args = self._parse_request(req)

            try:
                ret = method(*args)
            except Exception as e:
                logging.exception('Error occured during RPC')
                self._send_error(str(e), msg_id)
            else:
                self._send_result(ret, msg_id)

    def _close(self):
        for i in range(self._concurrency):
            self._queue.put(StopIteration)  # let _process_thread finish
        for thread in self._threads:
            thread.join()
        self._channel.close()

    def __call__(self, channel):
        self._channel = channel

        self.init()
        self._start_processors()

        while True:
            try:
                req = self._channel.get()
            except EOFError:
                # EOFError means client side process closed channel
                self._close()
                break
            else:
                # process async
                self._queue.put(req)

    def _parse_request(self, req):
        msg_id, method_name, args = req

        if method_name.startswith('_') or method_name == 'init':
            raise ValueError()

        if not hasattr(self, method_name):
            raise ValueError()

        method = getattr(self, method_name)
        if not method:
            raise ValueError()

        if not hasattr(method, '__call__'):
            raise ValueError()

        return (msg_id, method, args)

    def _send_error(self, error, msg_id):
        msg = (msg_id, error, None)
        self._send(msg)

    def _send_result(self, ret, msg_id):
        msg = (msg_id, None, ret)
        self._send(msg)

    def _send(self, msg):
        self._channel.put(msg)


class IPCRPCClient(object):
    def __init__(self, channel):
        self._channel = channel

        self._result = {}
        self._msg_id = 0

        self._callback_threads = []
        self._msg_id_queue = Queue()
        self._response_receiver = gevent.spawn(self._receive)

    def _receive(self):
        r_queue = deque([])
        id2future = {}

        while True:
            msg_id, future = self._msg_id_queue.get()
            if msg_id == 0:
                break  # msg_id=0 is closing signal from close()
            id2future[msg_id] = future

            unprocessed = deque([])

            while 0 < len(id2future): 
                if len(r_queue) == 0:
                    r_queue.append(self._channel.get())
                msg_id, error, result = r_queue.popleft()

                if msg_id not in id2future:
                    unprocessed.append((msg_id, error, result))
                    break

                # set future value
                if error:
                    id2future[msg_id].set(StandardError(error))
                else:
                    id2future[msg_id].set(result)

                del id2future[msg_id]

            for response in unprocessed:
                r_queue.append(response)

    def close(self):
        assert self._channel is not None

        for gthread in self._callback_threads:
            gthread.join()

        self._msg_id_queue.put([0, None])  # will shut recv thread down

        self._response_receiver.join()
        self._channel.close()
        self._channel = None

    def call(self, method_name, *args):
        """block until receiver thread set future value"""
        future = self.call_async(method_name, *args)
        return future.get()

    def call_callback(self, callback, method_name, *args):
        def _call_callback():
            callback(self.call(method_name, *args))
        gthread = gevent.spawn(_call_callback)
        self._callback_threads.append(gthread)

    def call_async(self, method_name, *args):
        assert self._channel is not None
        req = self._create_request(method_name, args)
        self._channel.put(req)  # send request

        msg_id = req[0]
        future = AsyncResult()
        self._msg_id_queue.put([msg_id, future])
        return future

    def _create_request(self, method_name, args):
        self._msg_id += 1
        req = (self._msg_id, method_name, args)
        return req
