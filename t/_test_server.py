# coding=utf-8

import logging

from tornado import ioloop

from trpc.server import RPCServer
from trpc.service import BaseService

log = logging.getLogger(__name__)


class Hello(BaseService):
    def hello(self, kk):
        print kk
        return "server return"


if __name__ == '__main__':
    RPCServer("127.0.0.1", 12315, Hello("hello world")).start_service()
    RPCServer("127.0.0.1", 12316, Hello("hello world")).start_service()
    RPCServer("127.0.0.1", 12317, Hello("hello world")).start_service()
    RPCServer("127.0.0.1", 12318, Hello("hello world")).start_service()
    RPCServer("127.0.0.1", 12319, Hello("hello world")).start_service()
    ioloop.IOLoop.instance().start()
