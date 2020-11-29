# install 

```bash
pip install -U git+https://github.com/sazima/tornado_request_mapping
```

# A simple example 

```python
import tornado.ioloop
from tornado.websocket import WebSocketHandler
import tornado.web
from tornado_request_mapping import request_mapping, Route


@request_mapping("/test")
class MainHandler(tornado.web.RequestHandler):
    @request_mapping('/get_by_id', method='get')
    async def test(self):
        self.write("Hello, world. get")

    @request_mapping('/update_by_id', method='post')
    async def test1(self):
        self.write("Hello, world. post")


@request_mapping('/t')
class MyHandler(tornado.web.RequestHandler):
    @request_mapping('/get_by_id', method='put')
    async def test(self):
        self.write("Hello, world. put")


@request_mapping("/ws")
class Wshandler(WebSocketHandler):
    def open(self, *args: str, **kwargs: str):
        print('open')

    def close(self, code: int = None, reason: str = None) -> None:
        print('close')

    def check_origin(self, origin: str) -> bool:
        return True


if __name__ == "__main__":
    app = tornado.web.Application()

    route = Route(app)
    route.register(MainHandler)
    route.register(MyHandler)
    route.register(Wshandler)

    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

```