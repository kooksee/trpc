# -*- coding: utf-8 -*-
import socket

from tornado.ioloop import IOLoop

from trpc.client import start_client
from trpc.server import start_server


class Manager(IOLoop):
    _services = {}

    def __init__(self):
        pass

    def add_server(self,
                   host='127.0.0.1',
                   port=8000,
                   handler=None,
                   ssl_options=None,
                   max_buffer_size=None,
                   read_chunk_size=None):
        start_server(
            host=host,
            port=port,
            handler=handler,
            ssl_options=ssl_options,
            max_buffer_size=max_buffer_size,
            read_chunk_size=read_chunk_size
        )

    def add_client(self,
                   name=None,
                   address=[("localhost", 12315)],
                   af=socket.AF_UNSPEC,
                   ssl_options=None,
                   max_buffer_size=None):
        start_client(
            name=name,
            address=address,
            af=af,
            ssl_options=ssl_options,
            max_buffer_size=max_buffer_size
        )

    def start_service(self):
        pass


if __name__ == '__main__':
    m = Manager()

    m.instance().start()
