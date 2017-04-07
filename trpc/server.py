# -*- coding: utf-8 -*-
import logging
import socket

import msgpack as packer
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer

log = logging.getLogger(__name__)


class ServerEntity(object):
    def __init__(self,
                 host="127.0.0.1",
                 port=8000,
                 handler=None,
                 conn=None,
                 family=socket.AF_UNSPEC,
                 backlog=128,
                 reuse_port=False):
        self.host = host
        self.port = port
        self.handler = handler
        self.conn = conn
        self.family = family
        self.backlog = backlog
        self.reuse_port = reuse_port


class ServerConnection(object):
    timeout = 5
    weight = 1
    EOF = b't\nr\np\nc'

    def __init__(self, stream, address, handler):
        self.stream = stream

        self.address = address
        self.handler = handler

        self.stream.set_close_callback(self.on_close)
        self.stream.read_until(self.EOF, self._on_message)

    def on_close(self):
        log.info("{} closed".format(self.address))

    def _on_message(self, _data):
        try:
            self.on_data(_data)
        except StreamClosedError:
            log.warning("lost client at host %s", self.address)
        except Exception as e:
            log.error(e.message)
        finally:
            self.stream.read_until(self.EOF, self._on_message)

    @gen.coroutine
    def on_data(self, _data):
        data, _ = _data.split(self.EOF)
        log.info("Received data: {}".format(data))
        if not data:
            log.error("data is null")
            return

        try:
            _id, _method, _data = packer.loads(data)
            method = getattr(self.handler, _method)
            if not method:
                log.warning("method {} not exist".format(_method))
                return

            result = method(_data)
            if not result:
                log.warning("method {} return null".format(_method))
                return

            yield self.stream.write(packer.dumps((_id, result)) + self.EOF)
        except Exception, e:
            log.error(e.message)


class RPCServer(TCPServer):
    _services = {}
    EOF = b't\nr\np\nc'
    server_entity = ServerEntity()

    def __init__(self,
                 host="127.0.0.1",
                 port=8000,
                 handler=None,
                 ssl_options=None,
                 max_buffer_size=None,
                 read_chunk_size=None,
                 family=socket.AF_UNSPEC,
                 backlog=128,
                 reuse_port=False):
        self.server_entity.host = host
        self.server_entity.port = port
        self.server_entity.handler = handler.initialize(self)
        self.server_entity.family = family
        self.server_entity.backlog = backlog
        self.server_entity.reuse_port = reuse_port

        TCPServer.__init__(
            self,
            ssl_options=ssl_options,
            max_buffer_size=max_buffer_size,
            read_chunk_size=read_chunk_size
        )

    def handle_stream(self, stream, address):
        ServerConnection(stream, address, self.server_entity.handler)

    def start_service(self):
        self.bind(
            self.server_entity.port,
            address=self.server_entity.host,
            family=self.server_entity.family,
            backlog=self.server_entity.backlog,
            reuse_port=self.server_entity.reuse_port
        )
        self.start(num_processes=1)
