#!/usr/bin/python
# -*- coding: utf-8 -*-
import gevent

from gipcrpc import starter_context, IPCRPCServer


class SumService(IPCRPCServer):
    def sum(self, a, b):
        return a + b


class MultiplyService(IPCRPCServer):
    def multiply(slef, a, b):
        return a * b


def main():
    # Using starter_context() and given IPCRPCServiceStarter object('context', in this sample)
    # is a good way to launch different service process.
    with starter_context() as context:
        # start new child process serving SumService methods(total process: 2, parent=1, child=1)
        client_for_sum = context.start(SumService)
        print 'sum(1, 2)=%d' % client_for_sum.call('sum', 1, 2)

        # start new child process serving MultiplyService(total process: 3, parent=1, child=2)
        client_for_multiply = context.start(MultiplyService)
        print 'multiply(3, 5)=%d' % client_for_multiply.call('multiply', 3, 5)

        # try sum again, created service is alive until with block closes
        print 'sum(3, 4)=%d' % client_for_sum.call('sum', 3, 4)

        # need more process? use 'n_process' parameter
        client_for_sum_p2 = context.start(SumService, n_process=2)
        print 'sum(10, 20)=%d' % client_for_sum_p2.call('sum', 10, 20)

    # at end of with, starter_context will wait for unfinished tasks
    # and shut down all sub processes
    # for now, total process is 1, only parent.


if __name__ == '__main__':
    gevent.spawn(main).join()
