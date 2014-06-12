#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import hashlib

def superhash(s):
    ret = s
    n = 3000
    md5 = lambda x: hashlib.md5(x).hexdigest()
    for i in xrange(n):
        ret = md5(ret)
    return ret


def main():
    t1 = time.time()
    for i in xrange(10000):
        superhash(str(i))
    t2 = time.time()
    print '%fsec' % (t2-t1)


if __name__ == '__main__':
    main()
