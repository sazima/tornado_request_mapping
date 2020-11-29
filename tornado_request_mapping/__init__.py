import inspect
from functools import partial
from typing import Optional

from tornado import gen
from tornado import iostream
from tornado.websocket import WebSocketHandler
from tornado.concurrent import future_set_result_unless_cancelled
from tornado.log import app_log
from tornado.web import _has_stream_request_body, Application, HTTPError

__all__ = ['request_mapping', 'Route']


class MethodNotAllowed(Exception):
    pass


class RouteNotInit(Exception):
    pass


class MissedDecorator(Exception):
    pass


class RequestMapping:
    allow_method = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self, value, method):
        if method not in self.allow_method:
            raise MethodNotAllowed()
        self.value = value
        self.method = method


def request_mapping(value: str, method: str = 'get'):
    def get_func(o, v: str):
        setattr(o, 'request_mapping', RequestMapping(v, method.lower()))
        if inspect.isclass(o):
            if not value.startswith('/'):
                app_log.warning("values should startswith / ")
            setattr(o, '_request_mapping_dict_', dict())
            o._execute = _execute
        return o

    return partial(get_func, v=value)


@gen.coroutine
def _execute(self, transforms, *args, **kwargs):
    """Executes this request with the given output transforms."""
    self._transforms = transforms
    try:
        if self.request.method not in self.SUPPORTED_METHODS:
            raise HTTPError(405)
        self.path_args = [self.decode_argument(arg) for arg in args]
        self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                for (k, v) in kwargs.items())
        # If XSRF cookies are turned on, reject form submissions without
        # the proper cookie
        if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                self.application.settings.get("xsrf_cookies"):
            self.check_xsrf_cookie()

        result = self.prepare()
        if result is not None:
            result = yield result
        if self._prepared_future is not None:
            future_set_result_unless_cancelled(self._prepared_future, None)
        if self._finished:
            return

        if _has_stream_request_body(self.__class__):
            try:
                yield self.request.body
            except iostream.StreamClosedError:
                return

        method_string = self._request_mapping_dict_.get(
            '_%s_request_mapping_%s' % (self.request.path, self.request.method.lower()))
        if not method_string:
            if self.request.method.lower() == 'options':
                method_string = 'options'
            else:
                raise HTTPError(405)
        method = getattr(self, method_string)
        result = method(*self.path_args, **self.path_kwargs)
        if result is not None:
            result = yield result
        if self._auto_finish and not self._finished:
            self.finish()
    except Exception as e:
        try:
            self._handle_request_exception(e)
        except Exception:
            app_log.error("Exception in exception handler", exc_info=True)
        finally:
            # Unset result to avoid circular references
            result = None
        if (self._prepared_future is not None and
                not self._prepared_future.done()):
            # In case we failed before setting _prepared_future, do it
            # now (to unblock the HTTP server).  Note that this is not
            # in a finally block to avoid GC issues prior to Python 3.4.
            self._prepared_future.set_result(None)


class Route:

    def __init__(self, app: Optional[Application] = None, prefix: str = ''):
        self.urls = list()
        self.app = app
        self.prefix = prefix
        self.host_handlers = []

    def register(self, handler):

        if not hasattr(handler, 'request_mapping'):
            raise MissedDecorator(
                "Please use request_mapping. See example: https://github.com/sazima/tornado_request_mapping")
        class_mapping = getattr(handler, 'request_mapping', None)  # type: RequestMapping
        if issubclass(handler, WebSocketHandler):
            self._add_mapping(handler, self.prefix + class_mapping.value, 'get', 'get')
            return
        for method_string in dir(handler):
            method = getattr(handler, method_string)
            if not hasattr(method, 'request_mapping'):
                continue
            method_mapping = getattr(method, 'request_mapping')  # type: RequestMapping
            full_path = self.prefix + class_mapping.value + method_mapping.value
            self._add_mapping(handler, full_path, method_mapping.method, method_string)

    def _add_mapping(self, handler, full_path, http_method, method_string):
        handler._request_mapping_dict_.update({
            '_%s_request_mapping_%s' % (full_path, http_method): method_string
        })
        host_handler = (
            r'{}'.format(full_path),
            handler
        )
        if self.app is not None:
            self.app.add_handlers(
                r".*",  # match any host
                [host_handler]
            )
        self.host_handlers.append(host_handler)

    def init_app(self, app):
        self.app = app
