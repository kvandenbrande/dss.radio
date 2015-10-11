import logging
from threading import Thread
import time
import urllib
import shout
import urllib2
import requests

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

        self.channel = shout.Shout()
        self.channel.mount = '/' + mountpoint

        self.api_host = options['api_host']
        self.channel.url = 'http://deepsouthsounds.com/'
        self.channel.name = title
        self.channel.genre = 'Deep House Music'
        self.channel.description = 'Deep sounds from the deep south'
        self.channel.format = options['ice_format']
        self.channel.host = options['ice_host']
        self.channel.port = int(options['ice_port'])
        self.channel.user = options['ice_user']
        self.channel.password = options['ice_password']
        self.channel.public = 1
        if self.channel.format == 'mp3':
            self.channel.audio_info = {
                'bitrate': str(320),
                'samplerate': str(48000),
                'channels': str(2),
            }

        self.server_url = 'http://' + self.channel.host + ':' + str(self.channel.port) + self.channel.mount
        print(self.server_url)

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
                audio = v['url']
                title = v['title']
                slug = v['slug']
                import urllib2
                try:
                    ret = urllib2.urlopen(audio)
                    if ret.code == 200:
                        found = True
                        ret = [{
                            'url': audio,
                            'description': title,
                            'slug': slug
                        }]
                except urllib2.HTTPError as ex:
                    pass
        except Exception as ex:
            logging.error(ex)
            ret = [{
                'url': 'https://dsscdn.blob.core.windows.net/mixes/52df41af-5f81-4f00-a9a8-9ffb5dc3185f.mp3',
                'description': 'Default song',
                'slug': '/'
            }]

        for p in ret:
            print("Playing {}".format(p))

        return ret

    def set_audio_queue(self, queue):
        self.audio_queue = queue
        self._ended = True

    def get_next_play_item(self):
        try:
            logging.debug("Finding next item")

            # get random item from DSS api
            if len(self.audio_queue) > self.audio_index:
                item = self.audio_queue[self.audio_index]
            else:
                item = self.default_queue()[0]

            self.channel.set_metadata({'song': str(item['description']), 'charset': 'utf-8'})
            logging.debug("Playing: {}".format(item['description']))
            self.stream = self.file_read_remote(item['url'])

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
