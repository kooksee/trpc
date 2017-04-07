# -*- coding: utf-8 -*-
import logging
import random
import socket
from functools import partial

import msgpack as packer
from tornado import gen
from tornado import ioloop
from tornado.concurrent import Future
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

from trpc.service import BaseService
from trpc.util import _IDGenerator

log = logging.getLogger(__name__)


class ClientEntity(object):
    def __init__(self,
                 name=None,
                 address=None,
                 handler=None,
                 conn=None,
                 af=socket.AF_UNSPEC,
                 ssl_options=None,
                 max_buffer_size=None):
        self.name = name
        self.address = address
        self.handler = handler
        self.conn = conn
        self.af = af
        self.ssl_options = ssl_options
        self.max_buffer_size = max_buffer_size


class ClientConnection(object):
    timeout = 5
    weight = 10
    EOF = b't\nr\np\nc'
    _req_id = {}
    _id = _IDGenerator()

    def __init__(self, stream, address, service, name=None):
        self.stream = stream

        self.address = address
        self.handler = BaseService()
        self.name = name
        self.service = service

        self.service._services[self.name][address] = self

        self.stream.set_close_callback(self.on_close)
        self.stream.read_until(self.EOF, self._on_message)

    def on_close(self):
        log.info("close {}".format(self.address))
        del self.service._services[self.name][self.address]
        if not self.service._services[self.name]:
            del self.service._services[self.name]

    def _on_message(self, _data):
        try:
            self.on_data(_data)
            self.stream.read_until(self.EOF, self._on_message)
            if self.weight < 10:
                self.weight += 1
        except StreamClosedError:
            log.warning("lost client at host %s", self.address)
            self.weight -= 1
        except Exception as e:
            log.error(e)
            self.weight -= 1

    def __write_callback(self, _id):
        log.info("{} write ok".format(_id))

    def __call(self, _method, _data):
        _id = next(self._id)
        self._req_id[_id] = Future()
        try:
            self.stream.write(packer.dumps((_id, _method, _data)) + self.EOF, partial(self.__write_callback, _id))
            if self.weight < 10:
                self.weight += 1
        except Exception, e:
            log.error(e)
            self.weight -= 1
        return self._req_id[_id]

    def __call__(self, _method, _data):
        return self.__call(_method, _data)

    def on_data(self, _data):
        try:
            data, _ = _data.split(self.EOF)
            _id, _data = packer.loads(data)
            self._req_id[_id].set_result(_data)
        except Exception, e:
            log.error(e)


class RPCClient(TCPClient):
    _services = {}
    client_entitys = {}

    def add_service(self,
                    name=None,
                    address=None,
                    af=socket.AF_UNSPEC,
                    ssl_options=None,
                    max_buffer_size=None):

        if name not in self._services:
            self._services[name] = {}

        self.client_entitys[name] = ClientEntity(
            name=name,
            address=address,
            af=af,
            ssl_options=ssl_options,
            max_buffer_size=max_buffer_size
        )

    @gen.coroutine
    def start_service(self):
        for client_entity in self.client_entitys.itervalues():
            for addr in client_entity.address:
                stream = yield self.connect(
                    addr[0],
                    addr[1],
                    af=client_entity.af,
                    ssl_options=client_entity.ssl_options,
                    max_buffer_size=client_entity.max_buffer_size
                )
                ClientConnection(stream, addr, self, name=client_entity.name)

    def __call__(self, service_name):

        b = {}
        for c in self._services[service_name].itervalues():
            if not b.get(c.weight):
                b[c.weight] = [c]
            else:
                b[c.weight].append(c)

        bk = b.keys()
        while 1:
            _r = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            for i in bk:
                if _r < i:
                    _d = random.choice(b[i])
                    return _d


def start_client(name=None,
                 address=None,
                 af=socket.AF_UNSPEC,
                 ssl_options=None,
                 max_buffer_size=None):
    rc = RPCClient()
    rc.add_service(
        name=name,
        address=address,
        af=af,
        ssl_options=ssl_options,
        max_buffer_size=max_buffer_size
    )
    rc.start_service()
    ioloop.IOLoop.instance().start()
