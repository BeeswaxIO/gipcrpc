#!/usr/bin/python
# -*- coding: utf-8 -*-
import gevent
import itertools
from unittest import TestCase
from nose.tools import ok_, eq_

from gipcrpc import child_service, IPCRPCServer

class MyService(IPCRPCServer):
    def sum(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b


class DelayService(IPCRPCServer):
    def delay(self, msec):
        gevent.sleep(msec / 1000.0)
        return msec


class BasicUsageTestCase(TestCase):
    def test_simple(self):
        def _test_simple():
            n_levels = (1, 2, 5, 10)
            c_levels = (1, 5, 10, 50)
            q_sizes = (None, 1, 5, 10, 50)

            for n, c, q in itertools.product(n_levels, c_levels, q_sizes):
                with child_service(MyService, n_process=n, concurrency=c, queue_size=q) as client:
                    value = client.call('sum', 5, 9)
                    eq_(value, 14)

                with child_service(MyService, concurrency=c, queue_size=q) as client:
                    future = client.call_async('sum', 3, 7)
                    value = future.get()
                    eq_(value, 10)

                cb_data = dict(value=None, called=False)
                with child_service(MyService, concurrency=c, queue_size=q) as client:
                    def _callback(value):
                        cb_data['value'] = value
                        cb_data['called'] = True

                    client.call_callback(_callback, 'sum', 1, 2)

                ok_(cb_data['called'])
                eq_(cb_data['value'], 3)

        gevent.spawn(_test_simple).join()

    def test_delay(self):
        def _test_delay():
            n_levels = (1, 2, 3, 4, 5)
            c_levels = (5, 10, 50)  # concurrency=1 can't pass this test on p=1
            q_sizes = (None, 5, 10, 50)

            for p, c, q in itertools.product(n_levels, c_levels, q_sizes):
                called = []

                with child_service(DelayService, n_process=p, concurrency=c, queue_size=q) as client:
                    def _cb(value):
                        print value
                        called.append(value)

                    client.call_callback(_cb, 'delay', 500)  # returns 3rd
                    gevent.sleep()
                    client.call_callback(_cb, 'delay', 100)  # returns 1st
                    gevent.sleep()
                    client.call_callback(_cb, 'delay', 300)  # returns 2nd

                eq_(called, [100, 300, 500])

        gevent.spawn(_test_delay).join()
