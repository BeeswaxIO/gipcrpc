#!/usr/bin/python
# -*- coding: utf-8 -*-


class IPCRPCMultiProcessClient(object):
    def __init__(self, clients):
        self._clients = tuple(clients)
        self._idx = 0

    def get_client(self, idx):
        assert 0 <= idx < len(self._clients)
        return self._clients[idx]

    def _choose_client(self):
        client = self._clients[self._idx]

        self._idx += 1
        if self._idx == len(self._clients):
            self._idx = 0

        return client

    def close(self):
        assert self._clients is not None
        for client in self._clients:
            client.close()
        self._clients = None

    def call_async(self, method_name, *args):
        client = self._choose_client()
        return client.call_async(method_name, *args)

    def call(self, method_name, *args):
        client = self._choose_client()
        return client.call(method_name, *args)

    def call_callback(self, callback, method_name, *args):
        client = self._choose_client()
        client.call_callback(callback, method_name, *args)
