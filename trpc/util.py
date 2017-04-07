# -*- coding: utf-8 -*-
import logging
import time

import redis

log = logging.getLogger(__name__)


def _IDGenerator():
    counter = 0
    while True:
        yield counter
        counter += 1
        if counter > (1 << 30):
            counter = 0


class _Callback():
    def __init__(self, _id):
        self._data = None
        self._id = _id
        self._c = redis.Redis(
            host="127.0.0.1",
            port=6379,
        )

    def __call__(self, data):

        self._data = data
        self._c.hset("test", self._id, data)

    def get_result(self, _id, timeout=15):
        _t = 0
        while 1:
            # print _t
            # print self._id
            # print self._data,"\n\n"
            if _t > timeout:
                log.error("timeout error")
                break

            time.sleep(0.01)
            d = self._c.hget("test", self._id)
            if not d:
                _t += 0.01
                continue

            return d
