#!/usr/bin/python
# -*- coding: utf-8 -*-
import gevent
from gipcrpc import IPCRPCServer


class MyService(IPCRPCServer):
    def sum(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b


class ConcatService(IPCRPCServer):
    def concat(self, strings, delimiter):
        return delimiter.join(strings)


class DelayService(IPCRPCServer):
    def delay(self, msec):
        gevent.sleep(msec / 1000.0)
        return msec
