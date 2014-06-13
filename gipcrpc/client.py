#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import deque
import gevent
from gevent.event import AsyncResult
from gevent.queue import Queue


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
