# coding=utf-8
import logging

from tornado import gen
from tornado import ioloop
from tornado.web import Application, RequestHandler

log = logging.getLogger(__name__)


class MainHandler(RequestHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        a = yield rpc_c("test")("hello", "hello, 我是客户端")
        print a
        self.write(str("pp"))
        self.finish()


if __name__ == '__main__':
    from trpc.client import RPCClient

    rpc_c = RPCClient()
    rpc_c.add_service(name="test", address=[
        ("127.0.0.1", 12315),
        ("127.0.0.1", 12316),
        ("127.0.0.1", 12317),
        ("127.0.0.1", 12318),
        ("127.0.0.1", 12319),
    ])
    rpc_c.start_service()
    # from torpc import RPCClient
    # rpc_client = RPCClient(('127.0.0.1', 5003), 'client2')

    handlers = [
        ("/", MainHandler)
    ]
    app = Application(handlers, **dict(
        xsrf_cookies=False,
        cookie_secret="jlogCFF@#$%^&*()(*^fcxfgs3245$#@$%^&*();'><,.<>FDRYTH$#$^%^&jlog",
        secret_key="123456@#$%^&*((*&^%$#%^&*&^%$##$%^&*(*&^%$#",
        debug=True
    ))
    app.listen(8088)

    # a = yield rpc_c("test")("hello", "234323132sds")
    # rpc_c("test")("hello", "234323132sds")
    # ioloop.PeriodicCallback(test, 100).start()
    # ioloop.IOLoop.current().add_callback(test)
    ioloop.IOLoop.instance().start()


    # from multiprocessing.pool import ThreadPool
    # from multiprocessing import Process, Manager
