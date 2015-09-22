from threading import Thread
import time
from deefuzzer import Player

BUF_LEN = 4096


class IceRelay(Thread):
    def __init__(self, client, title='DeepSouthSounds Radio'):
        super(IceRelay, self).__init__()
        self.title = title
        self.s = client
        self._ended = True
        self.player = Player("icecast")
        self.isOpen = True
        self.audio_queue = []
        self.audio_index = 0

        self.default_queue = [
            'https://dsscdn.blob.core.windows.net/mixes/7568d3a4-9a9f-4f0f-a900-f84231c26c47.mp3'
        ]

    def stop(self):
        self._ended = True

    def set_audio_queue(self, queue):
        self.audio_queue = queue

    def get_next_play_item(self):
        print "Finding next item"
        self._ended = False

        # get random item from DSS api
        if len(self.audio_queue) > self.audio_index:
            item = self.audio_queue[self.audio_index]
        else:
            item = self.default_queue[0]

        self.player.set_media(item)
        print "Playing: {}".format(item)
        return self.player.file_read_remote()

    def close_channel(self):
        self.isOpen = False

    def run(self):
        while True:
            now_playing = self.get_next_play_item()
            if now_playing is not None:
                for chunk in now_playing:
                    try:
                        self.s.s.send(chunk)
                        self.s.s.sync()
                    except Exception as ex:
                        print ("Error sending chunk: {0}".format(ex))
                        self.close_channel()
                    if self._ended:
                        break
            else:
                print("No audio, waiting")
                time.sleep(5)
