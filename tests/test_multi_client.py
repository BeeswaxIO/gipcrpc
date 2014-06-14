#!/usr/bin/python
# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.tools import ok_, eq_, raises


from gipcrpc import IPCRPCMultiProcessClient


class DummyClient(object):
    def __init__(self, _id):
        self._id = _id
        self.reset()

    def reset(self):
        self.called = False
        self.called_method = None
        self.params = None

    def call(self, method_name, *args):
        self.called = True
        self.called_method = 'call'
        self.params = dict(method_name=method_name, args=args)

    def call_async(self, method_name, *args):
        self.called = True
        self.called_method = 'call_async'
        self.params = dict(method_name=method_name, args=args)

    def call_callback(self, callback, method_name, *args):
        self.called = True
        self.called_method = 'call_callback'
        self.params = dict(callback=callback, method_name=method_name, args=args)

    def close(self):
        self.called = True
        self.called_method = 'close'
        self.params = dict()


class MultiClientTestCase(TestCase):
    def _create_clients(self, n):
        return [DummyClient(i + 1) for i in xrange(n)]

    def test_construct(self):
        client_num = [1, 2, 5, 10]
        for n in client_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)
            ok_(type(mclient._clients) is tuple)
            eq_(len(mclient._clients), len(clients))
            eq_(mclient._idx, 0)

    def test_get_client(self):
        client_num = [1, 2, 5, 10]
        for n in client_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)

            for i in xrange(n):
                exppected_client = clients[i]
                result_client = mclient.get_client(i)
                ok_(result_client is exppected_client)

    @raises(AssertionError)
    def test_get_client_bad_index_negative(self):
        clients = self._create_clients(2)
        mclient = IPCRPCMultiProcessClient(clients)
        mclient.get_client(-1)  # raises

    @raises(AssertionError)
    def test_get_client_bad_index_positive(self):
        clients = self._create_clients(2)
        mclient = IPCRPCMultiProcessClient(clients)
        mclient.get_client(2)  # raises

    def test_close(self):
        client_num = [1, 2, 5, 10]
        for n in client_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)
            for c in clients:
                assert c.called is False
            mclient.close()
            for c in clients:
                ok_(c.called and c.called_method == 'close')

    @raises(AssertionError)
    def test_close_multiple_times_closing(self):
        clients = self._create_clients(2)
        mclient = IPCRPCMultiProcessClient(clients)
        mclient.close()  # ok
        mclient.close()  # raises

    def test_choose_client(self):
        # clients=1 case
        clients1 = self._create_clients(1)
        mclient1 = IPCRPCMultiProcessClient(clients1)

        eq_(mclient1._idx, 0)
        c1_1 = mclient1._choose_client()
        ok_(c1_1 is clients1[0])
        eq_(mclient1._idx, 0)
        c1_2 = mclient1._choose_client()
        ok_(c1_2 is clients1[0])

        # clients=N(1 < N) case
        clients_num = (2, 5, 10)
        for n in clients_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)

            for i in xrange(n - 1):
                eq_(mclient._idx, i)
                c = mclient._choose_client()
                ok_(c is clients[i])
                eq_(mclient._idx, i + 1)

            eq_(mclient._idx, n - 1)
            c = mclient._choose_client()
            eq_(c, clients[-1])
            eq_(mclient._idx, 0)

    def test_call(self):
        clients_num = (2, 5, 10)
        for n in clients_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)

            for i in xrange(n):
                c = clients[i]
                assert not c.called
                mclient.call('foobar', i, i * 2)
                ok_(c.called)
                eq_(c.called_method, 'call')
                eq_(c.params, dict(method_name='foobar', args=(i, i*2)))

                total_called = len([c for c in clients if c.called])
                eq_(total_called, i + 1)

    def test_call_async(self):
        clients_num = (2, 5, 10)
        for n in clients_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)

            for i in xrange(n):
                c = clients[i]
                assert not c.called
                mclient.call_async('foobar', i, i * 2)
                ok_(c.called)
                eq_(c.called_method, 'call_async')
                eq_(c.params, dict(method_name='foobar', args=(i, i*2)))

                total_called = len([c for c in clients if c.called])
                eq_(total_called, i + 1)

    def test_call_callback(self):
        clients_num = (2, 5, 10)
        for n in clients_num:
            clients = self._create_clients(n)
            mclient = IPCRPCMultiProcessClient(clients)

            for i in xrange(n):
                c = clients[i]
                assert not c.called
                def _dummy(value):
                    pass 
                mclient.call_callback(_dummy, 'foobar', i, i * 2)
                ok_(c.called)
                eq_(c.called_method, 'call_callback')
                eq_(c.params, dict(method_name='foobar', callback=_dummy, args=(i, i*2)))

                total_called = len([c for c in clients if c.called])
                eq_(total_called, i + 1)
