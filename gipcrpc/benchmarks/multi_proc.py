#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import hashlib
import gevent

from gipcrpc import child_service, IPCRPCServer


class MyService(IPCRPCServer):
    def superhash(self, s):
        n = 3000
        md5 = lambda x: hashlib.md5(x).hexdigest()
        ret = s
        for i in xrange(n):
            ret = md5(ret)
        return ret


count = 0


def main():
    t1 = time.time()
    n = 10000
    with child_service(MyService, n_process=8, concurrency=1) as client:

        for i in xrange(n):
            arg = str(i)
            def _cb(value):
                global count
                count += 1
                # print '%s count=%d' % (value, count)
            client.call_callback(_cb, 'superhash', arg)

        def _waiter():
            global count
            while count < n:
                gevent.sleep(0.1)

        waiter = gevent.spawn(_waiter)
        waiter.join()
        t2 = time.time()
        print '%fsec' % (t2-t1)


if __name__ == '__main__':
    gevent.spawn(main).join()
