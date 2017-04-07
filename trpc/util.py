# -*- coding: utf-8 -*-


def _IDGenerator():
    counter = 0
    while True:
        yield counter
        counter += 1
        if counter > (1 << 30):
            counter = 0
