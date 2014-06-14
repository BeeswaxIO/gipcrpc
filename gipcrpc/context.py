#!/usr/bin/python
# -*- coding: utf-8 -*-
import gipc
from contextlib import contextmanager

from client import IPCRPCClient
from multi_client import IPCRPCMultiProcessClient


_internal_pid = 0


@contextmanager
def child_service(klass, n_process=1, concurrency=10, queue_size=None):
    with starter_context() as context:
        client = context.start(
            klass, concurrency=concurrency, queue_size=queue_size, n_process=n_process)
        yield client


@contextmanager
def starter_context():
    context = IPCRPCServiceStarter()
    try:
        yield context
    finally:
        context.close()


def fork_service(klass, concurrency=10, queue_size=None):
    """simply create service process, returns tuple like (service_process, client)
    you can communicate through client's call/call_async/call_callback methods.
    when you use fork_service(), please make sure to call
    client.close() and service_process.join()"""
    global _internal_pid
    _internal_pid += 1
    child_ch, parent_ch = gipc.pipe(duplex=True)
    service = klass()
    args = (child_ch, _internal_pid, concurrency, queue_size)
    service_process = gipc.start_process(target=service, args=args)

    client = IPCRPCClient(parent_ch)
    return (service_process, client)


class IPCRPCServiceStarter(object):
    def __init__(self):
        self._service_processes = []
        self._clients = []

    def start(self, klass, concurrency=10, queue_size=None, n_process=1):
        assert 0 < n_process
        if n_process == 1:
            return self._start_single(klass, concurrency, queue_size)
        else:
            return self._start_multi(klass, n_process, concurrency, queue_size)

    def _start_single(self, klass, concurrency, queue_size):
        (service_process, client) = fork_service(klass, concurrency, queue_size)
        self._service_processes.append(service_process)
        self._clients.append(client)
        return client

    def _start_multi(self, klass, n_process, concurrency, queue_size):
        assert 1 < n_process
        clients = []
        for i in xrange(n_process):
            (service_process, client) = fork_service(klass, concurrency, queue_size)
            self._service_processes.append(service_process)
            clients.append(client)
        multi_client = IPCRPCMultiProcessClient(clients)
        self._clients.append(multi_client)
        return multi_client

    def close(self):
        for client in self._clients:
            client.close()
        for service_process in self._service_processes:
            service_process.join()
