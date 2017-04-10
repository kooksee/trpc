# -*- coding: utf-8 -*-
import random


def _IDGenerator():
    counter = 0
    while True:
        yield counter
        counter += 1
        if counter > (1 << 30):
            counter = 0


class LoadBance(object):
    __weight = {}
    _rc = range(10)

    def set_weight(self, name, key, weight=10):
        if name not in self.__weight:
            self.__weight[name] = {}
        self.__weight[name][key] = weight

    def increase(self, name, key):
        if self.__exist(name, key):
            self.__weight[name][key] += 1

    def decrease(self, name, key):
        if self.__exist(name, key):
            self.__weight[name][key] -= 1

    def get_key(self, name):
        _r = 0
        while 1:
            if _r >= 5:
                return

            w_ks = self.__weight[name]
            _r = random.choice(self._rc)
            its = w_ks.items()
            random.shuffle(its)
            for key, weight in its:
                if _r <= weight:
                    return key

            _r += 1

    def __exist(self, name, key):
        return name in self.__weight and key in self.__weight[name][key]

    def del_key(self, name, key):
        if self.__exist(name, key):
            del self.__weight[name][key]


class TRPCException(Exception):
    def __init__(self, _code=None, _msg=None):
        self._msg = _msg
        self.code = _code

    def get(self):
        return self.code, self._msg

    def __str__(self):
        return self._msg

    def __repr__(self):
        return self._msg
