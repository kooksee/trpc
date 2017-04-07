# coding=utf-8
import logging
from threading import Thread

from tornado import gen
from tornado import ioloop
from tornado.web import Application, RequestHandler

log = logging.getLogger(__name__)


class MainHandler(RequestHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        a = yield rpc_c("test")("hello", "hello, 我是客户端")
        print a
        self.write(str("ok"))
        self.finish()


def test():
    def __test():
        import requests
        r = requests.get("http://127.0.0.1:8088/")
        print r.text

    def _test():
        Thread(target=__test).start()

    ioloop.PeriodicCallback(_test, 100).start()


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

    ioloop.IOLoop.instance().add_callback(test)
    ioloop.IOLoop.instance().start()
