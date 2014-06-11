#!/usr/bin/python
# -*- coding: utf-8 -*-
import gevent

from gipcrpc import child_service, IPCRPCServer

# define your RPC service by inheritance
class MyService(IPCRPCServer):

    # instance method name will matter!
    # client object's call/call_async/call_callback will take that name as RPC method name
    def sum(self, a, b):
        return a + b


def main():
    # 'concurrency' will control simultaneous processing gleenlet number on service
    with child_service(MyService, concurrency=10) as client:
        # async callback
        def _callback(value):
            print '_callback: value=%d' % value
        client.call_callback(_callback, 'sum', 1, 2)

        # blocking call
        print 'block call: value=%d' % client.call('sum', 2, 3)

        # future(gevent.event.AsyncResult object)
        future = client.call_async('sum', 10, 20)
        print 'future: value=%d' % future.get()  # will block until service side computation finishes


if __name__ == '__main__':
    gevent.spawn(main).join()

