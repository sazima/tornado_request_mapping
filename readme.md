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
    async def test111(self):
        self.write("Hello, world. post")
    
    @request_mapping("/(\d{4})/(\d{2})/(\d{2})/([a-zA-Z\-0-9\.:,_]+)/?")
    async def many_args(self, year, month, day, slug):
        # http://localhost:8888/test/2020/11/11/123
        print(year, month, day, slug)
        self.write(f"{year} / {month} / {day} , {slug}")


@request_mapping('/t')
class MyHandler(tornado.web.RequestHandler):
    @request_mapping('/get_by_id', method='put')
    async def test111(self):
        self.write("Hello, world. put")


if __name__ == "__main__":
    app = tornado.web.Application()

    route = Route(app)
    route.register(MainHandler)
    route.register(MyHandler)

    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

```

