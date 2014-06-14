#!/usr/bin/python
# -*- coding: utf-8 -*-
import itertools
from unittest import TestCase
from nose.tools import eq_, ok_


from dummy_services import MyService


class DummySendingChannel(object):
    def __init__(self):
        self.called = False
        self.msg = None

    def put(self, msg):
        self.called = True
        self.msg = msg


class ServerTestCase(TestCase):

    def test_configure(self):
        ipids = (1, 3, 10)
        c_levels = (1, 5, 10, 50)
        q_sizes = (None, 1, 5, 10, 50)
        for ipid, c, q in itertools.product(ipids, c_levels, q_sizes):
            my_service = MyService()
            assert not hasattr(my_service, '_queue_size')
            assert not hasattr(my_service, '_concurrency')
            assert not hasattr(my_service, '_internal_pid')
            
            my_service._configure(ipid, c, q)
            eq_(my_service._queue_size, q)
            eq_(my_service._concurrency, c)
            eq_(my_service._internal_pid, ipid)

    def test_send(self):
        my_service = MyService()
        ch = DummySendingChannel()
        assert not hasattr(my_service, '_channel')
        assert not ch.called
        my_service._channel = ch

        dummy_result = (1, None, 123)
        my_service._send(dummy_result)

        ok_(ch.called)
        eq_(ch.msg, dummy_result)

    def test_send_error(self):
        my_service = MyService()
        ch = DummySendingChannel()
        assert not hasattr(my_service, '_channel')
        assert not ch.called
        my_service._channel = ch

        err_msg = str(StandardError('we had a serious error'))
        my_service._send_error(err_msg, 23)
        ok_(ch.called)
        eq_(ch.msg, (23, err_msg, None))

    def test_send_result(self):
        my_service = MyService()
        ch = DummySendingChannel()
        assert not hasattr(my_service, '_channel')
        assert not ch.called
        my_service._channel = ch

        dummy_result = 'a,b,c'
        my_service._send_result(dummy_result, 34)
        ok_(ch.called)
        eq_(ch.msg, (34, None, dummy_result))
