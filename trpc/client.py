# -*- coding: utf-8 -*-
import logging
import socket
from functools import partial

import msgpack as packer
from tornado import gen
from tornado import ioloop
from tornado.concurrent import Future
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

from trpc.util import _IDGenerator, LoadBance

log = logging.getLogger(__name__)


class ClientConnection(object):
    timeout = 5
    weight = 10
    EOF = b't\nr\np\nc'
    _req_id = {}
    _id = _IDGenerator()

    def __init__(self,
                 conn=None,
                 lb=None,
                 addr=None,
                 name=None,
                 af=socket.AF_UNSPEC,
                 ssl_options=None,
                 max_buffer_size=None,
                 retry=5):

        self.lb = lb

        self.stream = None
        self.retry = retry
        self.conn = conn
        self.addr = addr
        self.host, self.port = addr
        self.name = name
        self.af = af
        self.ssl_options = ssl_options
        self.max_buffer_size = max_buffer_size

        self.__try_connect_task = ioloop.PeriodicCallback(self.__conn, 1000)

    @gen.coroutine
    def start(self):
        self._conn()

    def on_close(self):
        self.stream = None
        self.lb.del_weight(self.name, self.addr)
        if not self.__try_connect_task.is_running():
            self.__try_connect_task.start()
        log.error("service {} {}:{} closed".format(self.name, self.host, self.port))

    @gen.coroutine
    def __conn(self):
        try:
            log.info("try to connect service {} {}:{}".format(self.name, self.host, self.port))
            self.stream = yield self.conn(
                self.host,
                self.port,
                af=self.af,
                ssl_options=self.ssl_options,
                max_buffer_size=self.max_buffer_size
            )
            self.stream.read_until(self.EOF, self._on_message)
            self.stream.set_close_callback(self.on_close)

            self.lb.set_weight(self.name, self.addr)

            if self.__try_connect_task.is_running():
                self.__try_connect_task.stop()

            log.info("connect to service {} {}:{} ok".format(self.name, self.host, self.port))

            return
        except StreamClosedError, e:
            self.lb.del_weight(self.name, self.addr)
            log.error(e)
        except Exception, e:
            self.lb.decrease(self.name, self.addr)
            log.error(e)

        if not self.__try_connect_task.is_running():
            self.__try_connect_task.start()
        self.stream = None

    def _conn(self):
        i = self.retry
        while i > 0:
            if self.stream:
                return

            self.__conn()
            i -= 1

    def _on_message(self, _data):
        try:
            self.on_data(_data)
            self.stream.read_until(self.EOF, self._on_message)
        except StreamClosedError, e:
            self.lb.del_weight(self.name, self.addr)
            log.error(e)
        except Exception as e:
            self.lb.decrease(self.name, self.addr)
            log.error(e)

    def __write_callback(self, _id):
        log.info("{} write ok".format(_id))

    def __call(self, _method, _data):
        _id = next(self._id)
        self._req_id[_id] = Future()
        _x = lambda: self.stream.write(
            packer.dumps((_id, _method, _data)) + self.EOF,
            partial(self.__write_callback, _id)
        )

        if self.stream:
            _x()
            self.lb.increase(self.name, self.addr)
        else:
            self.__conn()
            if self.stream:
                _x()
                self.lb.increase(self.name, self.addr)
            else:
                self._req_id[_id].set_result(None)

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


class ClientEntity(object):
    def __init__(self,
                 name=None,
                 conns=None):
        self.name = name
        self.conns = conns


class RPCClient(TCPClient):
    client_entitys = {}
    lb = LoadBance()

    def add_service(self,
                    name=None,
                    address=None,
                    af=socket.AF_UNSPEC,
                    ssl_options=None,
                    max_buffer_size=None):

        self.client_entitys[name] = ClientEntity(
            name=name,
            conns={addr: ClientConnection(
                conn=self.connect,
                lb=self.lb,
                addr=addr,
                name=name,
                af=af,
                ssl_options=ssl_options,
                max_buffer_size=max_buffer_size
            ) for addr in address}
        )

    @gen.coroutine
    def start_service(self):
        for name, client_entity in self.client_entitys.iteritems():
            for addr, conn in client_entity.conns.iteritems():
                self.lb.set_weight(name, addr)
                conn.start()

    @gen.coroutine
    def __call__(self, service_name, _method, _data):
        addr = self.lb.get_key(service_name)
        if not addr:
            log.error("can not find service {}".format(service_name))
            raise gen.Return()

        _conn = self.client_entitys[service_name].conns.get(addr)
        _res = yield _conn(_method, _data)
        if not _res:
            raise gen.Return()

        raise gen.Return(_res)
