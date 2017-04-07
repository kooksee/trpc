# -*- coding: utf-8 -*-


class BaseService(object):
    service = None

    def __init__(self, *args, **kwargs):
        pass

    def initialize(self, service):
        self.service = service
        return self

    def emit(self):
        pass

