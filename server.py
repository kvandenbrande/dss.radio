import logging
import os
import signal
import time
import tornado
import tornado.ioloop
import tornado.web
import tornado.escape
from tornado.options import define, options, parse_command_line

from ice_relay import IceRelay

is_closing = False


class MainHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render("index.html")


class ShuffleAudioHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        try:
            relay.shuffle_queue()
        except Exception, ex:
            raise tornado.web.HTTPError(500, ex.message)

class PlayAudioHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        try:
            data = tornado.escape.json_decode(self.request.body)
            in_file = data.get('audio_file')
            if in_file is not None:
                relay.set_audio_queue([in_file])
        except Exception, ex:
            raise tornado.web.HTTPError(500, ex.message)


class StopAudioHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        try:
            relay.channel_close()
        except Exception, ex:
            raise tornado.web.HTTPError(500, ex.message)


def signal_handler(signum, frame):
    global is_closing
    logging.info('exiting...')
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        relay.channel_close()

        tornado.ioloop.IOLoop.instance().stop()
        logging.info('exit success')

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")

define("ice_host", default='localhost', help="Icecast server host")
define("ice_port", default=8000, help="Icecast server port")
define("ice_user", default='source', help="Icecast user")
define("ice_password", default='hackme', help="Icecast password")
define("ice_mount", default='/mp3', help="Default icecast mount point")
define("ice_format", default='mp3', help="Format of the icecast server (mp3, vorbis, flac)")
define("ice_protocol", default='http', help="Protocol (currently only http)")
define("api_host", default='api.deepsouthsounds.com', help="API Host for serving audio")

#tornado.options.parse_command_line()
tornado.options.parse_config_file("dss.radio.conf")
relay = IceRelay(options=options)


def main():
    if relay.channel_open():
        relay.start()
    else:
        logging.error("IceCast relay failed to start")
        exit()

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/a/play", PlayAudioHandler),
            (r"/a/stop", StopAudioHandler),
            (r"/a/shuffle", ShuffleAudioHandler),
        ],
        cookie_secret="6f294734-215d-4f98-82e9-8e6ca500f524",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        # xsrf_cookies=True,
        debug=options['debug']
    )
    signal.signal(signal.SIGINT, signal_handler)
    app.listen(options['port'])
    tornado.ioloop.PeriodicCallback(try_exit, 100).start()
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
