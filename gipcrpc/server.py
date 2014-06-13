#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import gevent
from gevent.queue import Queue


class IPCRPCServer(object):
    def __init__(self):
        pass

    def init(self):
        """subclass can initialize something here,
        will be called after fork()"""
        pass

    def _configure(self, internal_pid, concurrency, queue_size):
        self._queue_size = queue_size
        self._concurrency = concurrency
        self._internal_pid = internal_pid

    def _start_processors(self):
        """you must call this method after fork()"""
        self._queue = Queue(self._queue_size)
        self._threads = []
        for i in range(self._concurrency):
            thread_id = i + 1
            thread = gevent.spawn(self._process_thread, thread_id)
            self._threads.append(thread)

    def _process_thread(self, thread_id):
        for req in self._queue:
            msg_id, method, args = self._parse_request(req)

            try:
                ret = method(*args)
            except Exception as e:
                logging.exception('[process:%d][worker:%d] Error occured during RPC' % (self._internal_pid, thread_id))
                self._send_error(str(e), msg_id)
            else:
                self._send_result(ret, msg_id)

    def _close(self):
        for i in range(self._concurrency):
            self._queue.put(StopIteration)  # let _process_thread finish
        for thread in self._threads:
            thread.join()
        self._channel.close()

    def __call__(self, channel, internal_pid, concurrency=10, queue_size=None):
        self._channel = channel
        self._configure(internal_pid, concurrency, queue_size)

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
            raise ValueError('No such method: %s' % method_name)

        if not hasattr(self, method_name):
            raise ValueError('No such method: %s' % method_name)

        method = getattr(self, method_name)
        if not hasattr(method, '__call__'):
            raise ValueError('Method \'%s\' is not callable' & method_name)

        return (msg_id, method, args)

    def _send_error(self, error, msg_id):
        msg = (msg_id, error, None)
        self._send(msg)

    def _send_result(self, ret, msg_id):
        msg = (msg_id, None, ret)
        self._send(msg)

    def _send(self, msg):
        self._channel.put(msg)
