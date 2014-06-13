#!/usr/bin/python
# -*- coding: utf-8 -*-
import gipc
from contextlib import contextmanager

from client import IPCRPCClient
from multi_client import IPCRPCMultiProcessClient


_internal_pid = 0


@contextmanager
def child_service(klass, n_process=1, concurrency=10, queue_size=None):
    global _internal_pid
    service_processes = []
    clients = []

    for i in range(n_process):
        child_ch, parent_ch = gipc.pipe(duplex=True)
        service = klass()
        _internal_pid += 1
        args = (child_ch, _internal_pid, concurrency, queue_size)
        service_process = gipc.start_process(target=service, args=args)
        service_processes.append(service_process)

        client = IPCRPCClient(parent_ch)
        clients.append(client)

    multi_client = IPCRPCMultiProcessClient(clients)
    try:
        yield multi_client
    finally:
        multi_client.close()
        for process in service_processes:
            process.join()
