#!/usr/bin/python
# -*- coding: utf-8 -*-
import itertools
import gevent
from unittest import TestCase
from nose.tools import ok_, eq_


from gipcrpc import fork_service, starter_context, IPCRPCServiceStarter
import gipcrpc.context


from dummy_services import MyService, ConcatService


class ContextTestCase(TestCase):

    def test_fork_and_internal_pid(self):
        def _test_fork_and_internal_pid():
            c_levels = (1, 2)
            q_sizes = (None, 1, 5)

            for c, q in itertools.product(c_levels, q_sizes):
                ipid = gipcrpc.context._internal_pid
                ok_(0 < ipid)

                try:
                    sp, client = fork_service(MyService)

                    for i in xrange(10):
                        a = i * 2 + 7
                        b = i * 3 + 5
                        expected = a + b
                        result = client.call('sum', a, b)
                        eq_(result, expected)

                finally:
                    client.close()
                    sp.join()

                ipid2 = gipcrpc.context._internal_pid
                eq_(ipid2, ipid + 1)

    def test_context_arg(self):
        def _test_context_arg():
            with starter_context() as context:
                ok_(type(context) is IPCRPCServiceStarter)
        gevent.spawn(_test_context_arg).join()

    def test_context_simple(self):
        def _test_context_simple():
            n_levels = (1, 2, 5, 10)
            c_levels = (1, 5, 10, 50)
            q_sizes = (None, 1, 5, 10, 50)
            for n, c, q in itertools.product(n_levels, c_levels, q_sizes):
                with starter_context() as context:
                    client = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=n)
                    value = client.call('sum', 5, 9)
                    eq_(value, 14)

                with starter_context() as context:
                    client = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=n)
                    future = client.call_async('sum', 3, 7)
                    value = future.get()
                    eq_(value, 10)

                cb_data = dict(value=None, called=False)
                with starter_context() as context:
                    client = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=n)

                    def _callback(value):
                        cb_data['value'] = value
                        cb_data['called'] = True

                    client.call_callback(_callback, 'sum', 1, 2)

            ok_(cb_data['called'])
            eq_(cb_data['value'], 3)

        gevent.spawn(_test_context_simple).join()

    def test_context_single_and_multi(self):
        def _test_context_single_and_multi():
            c_levels = (1, 5, 10, 50)
            q_sizes = (None, 1, 5, 10, 50)
            for c, q in itertools.product(c_levels, q_sizes):
                with starter_context() as context:
                    # fork 1 process first
                    client1 = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=1)
                    value1 = client1.call('sum', 1, 2)
                    eq_(value1, 3)

                    # fork multi processes
                    np = 5
                    client2 = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=2)
                    for i in xrange(np):
                        a = i + 1
                        b = i * 2 + 3
                        expected = a + b
                        result = client2.call('sum', a, b)
                        ok_(result, expected)

                    value2 = client1.call('sum', 10, 22)
                    eq_(value2, 32)

        gevent.spawn(_test_context_single_and_multi).join()

    def test_context_multiple_calls(self):
        def _test_context_multiple_calls():
            n_levels = (1, 2, 5, 10)
            c_levels = (1, 5, 10, 50)
            q_sizes = (None, 1, 5, 10, 50)
            for n, c, q in itertools.product(n_levels, c_levels, q_sizes):
                with starter_context() as context:
                    client = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=n)

                    for i in xrange(10):
                        a = i * 2 + 1
                        b = i * 3 + 13
                        expected = a + b
                        result = client.call('sum', a, b)
                        eq_(result, expected)

        gevent.spawn(_test_context_multiple_calls).join()

    def test_context_multi_services(self):
        def _test_context_multi_services():
            n_levels = (1, 2)
            c_levels = (1, 2)
            q_sizes = (None, 1, 5)
            for n, c, q in itertools.product(n_levels, c_levels, q_sizes):
                with starter_context() as context:
                    client1 = context.start(MyService,
                        concurrency=c, queue_size=q, n_process=n)
                    value1 = client1.call('sum', 5, 9)
                    eq_(value1, 14)

                    client2 = context.start(ConcatService,
                        concurrency=c, queue_size=q, n_process=n)
                    value2 = client2.call('concat', ['a', 'b', 'c'], ',')
                    eq_(value2, 'a,b,c')

        gevent.spawn(_test_context_multi_services).join()
