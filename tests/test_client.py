#!/usr/bin/python
# -*- coding: utf-8 -*-
import itertools
import logging
import gevent
from unittest import TestCase
from nose.tools import ok_, eq_

from gipcrpc import fork_service, IPCRPCClient


from dummy_services import MyService


class ClientTestCase(TestCase):
    def test_msg_id(self):
        def _test_msg_id():
            c_levels = (1, 5, 10, 50)
            q_sizes = (None, 1, 5, 10, 50)
            for c, q in itertools.product(c_levels, q_sizes):
                try:
                    sp, client = fork_service(MyService,
                        concurrency=c, queue_size=q)
                    ok_(type(client) is IPCRPCClient)
                    eq_(client._msg_id, 0)

                    client.call('sum', 1, 2)
                    eq_(client._msg_id, 1)

                    client.call_async('sum', 5, 6)
                    eq_(client._msg_id, 2)

                    def _cb(value):
                        pass
                    client.call_callback(_cb, 'sum', 8, 9)
                    eq_(client._msg_id, 3)
                except:
                    logging.exception('error')
                    raise
                finally:
                    client.close()
                    sp.join()

        gevent.spawn(_test_msg_id).join()
