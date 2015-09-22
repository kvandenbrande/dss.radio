#!/usr/bin/env python

import shout


class IceClient(object):
    def __init__(self, host, port, user, password, mount, format, protocol):

        self.s = shout.Shout()
        print "Using libshout version {}".format(shout.version())

        self.s.host = host
        self.s.port = port
        self.s.user = user
        self.s.password = password
        self.s.mount = mount
        self.s.format = format
        self.s.protocol = protocol
        self.s.open()

    def stop(self):
        self.s.close()

"""
if __name__ == '__main__':
    streamer = IceClient(
        host='niles',
        port=8999,
        user='source',
        password='hackme',
        mount="/pyshout",
        format='mp3',
        protocol='http'
    )
    streamer.play_audio(['/home/fergalm/Dropbox/BT_The_Moment_of_Truth.mp3'])
"""
