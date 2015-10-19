import logging
from threading import Thread
import time
import urllib
import shout
import urllib2
import requests
from util.social import Twitter

BUF_LEN = 4096


class IceRelay(Thread):
    server_ping = False

    def __init__(self, options, mountpoint='dss', title='DeepSouthSounds Radio'):
        super(IceRelay, self).__init__()
        self.title = title
        self._ended = True
        self.isOpen = True
        self.audio_queue = []
        self.audio_index = 0

        self.channelIsOpen = False

        self.options = options
        self.mountpoint = mountpoint
        self.title = title

        self.api_host = options['api_host']
        self.api_callback_url = options['api_callback_url']

        self.twitter_consumer_key = options['twitter_consumer_key']
        self.twitter_consumer_secret = options['twitter_consumer_secret']
        self.twitter_access_token = options['twitter_access_token']
        self.twitter_access_token_secret = options['twitter_access_token_secret']

        self._channel_mutex = False

        self._open_channel()
        self.server_url = 'http://' + self.channel.host + ':' + str(self.channel.port) + self.channel.mount
        print(self.server_url)

    def _open_channel(self):
        self.channel = shout.Shout()
        self.channel.mount = '/' + self.mountpoint
        self.channel.url = 'http://deepsouthsounds.com/'
        self.channel.name = self.title
        self.channel.genre = 'Deep House Music'
        self.channel.description = 'Deep sounds from the deep south'
        self.channel.format = self.options['ice_format']
        self.channel.host = self.options['ice_host']
        self.channel.port = int(self.options['ice_port'])
        self.channel.user = self.options['ice_user']
        self.channel.password = self.options['ice_password']
        self.channel.public = 1
        if self.channel.format == 'mp3':
            self.channel.audio_info = {
                'bitrate': str(320),
                'samplerate': str(48000),
                'channels': str(2),
            }

    def channel_open(self):
        if self.channelIsOpen:
            return True

        try:
            self.channel.open()
            self.channelIsOpen = True
            return True
        except Exception as ex:
            logging.error('channel could not be opened: {}'.format(ex))

        return False

    def channel_close(self):
        self.channelIsOpen = False
        self._ended = True
        try:
            self.channel.close()
            logging.info('channel closed')
        except Exception as ex:
            logging.error('channel could not be closed: {}'.format(ex))

    def ping_server(self):
        log = True

        while not self.server_ping:
            try:
                server = urllib.urlopen(self.server_url)
                self.server_ping = True
                logging.info('Channel available.')
            except:
                time.sleep(1)
                if log:
                    logging.error('Could not connect the channel.  Waiting for channel to become available.')
                    log = False

    def default_queue(self):
        ret = []
        try:
            found = False
            while not found:
                r = requests.get('http://{}/_radio?rmix=z'.format(self.api_host))
                v = r.json()
                import urllib2
                try:
                    ret = urllib2.urlopen(v['url'])
                    if ret.code == 200:
                        found = True
                        ret = [v]
                except urllib2.HTTPError as ex:
                    pass
        except Exception as ex:
            logging.error(ex)
            ret = [{
                'url': 'https://dsscdn.blob.core.windows.net/mixes/52df41af-5f81-4f00-a9a8-9ffb5dc3185f.mp3',
                'title': 'Default song',
                'slug': '/'
            }]

        for p in ret:
            print("Playing {}".format(p))

        return ret

    def shuffle_queue(self):
        self._ended = True
        time.sleep(10)

    def set_audio_queue(self, queue):
        self.audio_queue = queue
        self._ended = True
        time.sleep(10)

    def get_next_play_item(self):
        try:
            logging.debug("Finding next item")

            # get random item from DSS api
            if len(self.audio_queue) > self.audio_index:
                item = self.audio_queue[self.audio_index]
            else:
                item = self.default_queue()[0]

            self.channel.set_metadata({'song': str(item['title']), 'charset': 'utf-8'})
            logging.debug("Playing: {}".format(item['title']))
            self.stream = self.file_read_remote(item['url'])
            
            self.post_callback(item['title'], item['slug'])

            if self.twitter_access_token and self.twitter_access_token_secret and \
               self.twitter_consumer_secret and self.twitter_consumer_key:
                try:
                    tw = Twitter(key=self.twitter_consumer_key, secret=self.twitter_consumer_secret,
                                 access_key=self.twitter_access_token, access_secret=self.twitter_access_token_secret)
                    tw.post("Now playing on DSS Radio - {}\nhttp://deepsouthsounds.com/".format(
                        item['title'][0:90]))
                except Exception as ex:
                    logging.debug("Unable to post to twitter: {}".format(ex))

            self._ended = False
            return True
        except Exception as ex:
            logging.error('Error getting next play item: {}'.format(ex))

        return False

    def run(self):
        self.ping_server()
        while True:
            now_playing = self.get_next_play_item()
            if now_playing is not None:

                for self.chunk in self.stream:
                    try:
                        self.channel.send(self.chunk)
                        self.channel.sync()
                    except shout.ShoutException as sex: #(snigger)
                        if not self._channel_mutex:
                            self.channelIsOpen = False
                            self._channel_mutex = True
                            self.channel_open()
                        else:
                            self._channel_mutex = False
                    except Exception as ex:
                        logging.error("Error sending chunk: {0}".format(ex))
                        self.channel_close()
                    if self._ended:
                        break
            else:
                logging.debug("No audio, waiting")
                time.sleep(5)

        print "Outta here........"

    def file_read_remote(self, item):
        """Read remote file and stream data through a generator."""
        main_buffer_size = 0x10000
        m = urllib2.urlopen(item)
        while True:
            __main_chunk = m.read(main_buffer_size)
            if not __main_chunk:
                break
            yield __main_chunk
        m.close()

    def post_callback(self, title, slug):
        if self.api_callback_url:
            url = "http://{}{}".format(self.api_host, self.api_callback_url.format(title, slug))
            r = requests.post(url)
            print (r)
