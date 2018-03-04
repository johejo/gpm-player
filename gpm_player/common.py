import platform
import subprocess
import tempfile
import warnings
import urllib.request

import vlc
from gmusicapi import Mobileclient, CallFailure
from inputimeout import inputimeout, TimeoutOccurred

from .exceptions import LoginFailure, PlayerExitException

if platform.system() == 'Windows':
    CLEAR_SCREEN = 'cls'
else:
    CLEAR_SCREEN = 'clear'


def clear_screen():
    subprocess.run(CLEAR_SCREEN, shell=True)
    print()


def print_track_info(info):
    length = int(info['durationMillis'])

    print('Title: {}\n'
          'Album: {}\n'
          'Artist: {}\n'
          'Length: {}m{}s\n'
          .format(info['title'], info['album'], info['artist'],
                  length // 1000 // 60, length // 1000 % 60))


def print_command_list():
    print('Command List\n'
          '\'q\': stop and quit\n'
          '\'p\': pause or play\n'
          '\'f\': go to next track\n'
          '\'b\': back to previous track\n'
          '\'r\': restart current track\n'
          '\'s\': back to station menu\n')


def print_bar(current, duration, remain, width=50):
    per = current / duration * 100
    bar = '█' * int(width * per / 100)

    print('Remaining play time: {} [s]'.format(remain))
    print(' {}% |{}| {}/{} {}\n'
          .format(round(per, 2), bar.ljust(width),
                  round(current / 1000, 2), duration / 1000, '[s]'))


def is_quit(cmd):
    if cmd in ('q', 'quit', 'exit'):
        return True
    else:
        return False


def is_next(cmd):
    if cmd in ('f', 'b', 'r', 's'):
        return True
    else:
        return False


def is_digit(cmd, length):
    if cmd.isdigit() and 0 <= int(cmd) <= length:
        return True
    else:
        return False


def choose_track_id(track):
    try:
        track_id = track['trackId']
    except KeyError:
        try:
            track_id = track['storeId']
        except KeyError:
            track_id = track['nid']

    return track_id


class BasePlayer(object):
    def __init__(self, *, email=None, password=None, interval=3, width=50):
        self.api = Mobileclient()
        self.vlc_media_player = vlc.MediaPlayer()
        self.interval = abs(interval)
        self.width = int(abs(width))

        if email is not None and password is not None:
            self._logged_in = False
            self.api_login(email, password)
        else:
            self._logged_in = False

    def api_login(self, email, password):
        attempts = 0

        while not self._logged_in and attempts < 3:
            self._logged_in = self.api.login(email, password,
                                             Mobileclient.FROM_MAC_ADDRESS)
            attempts += 1

    def close(self):
        if self._logged_in:
            self.api.logout()

    def prepare(self):
        if not self._logged_in:
            msg = 'Login is not completed.'
            warnings.warn(msg)

        if not self.api.is_authenticated():
            raise LoginFailure

    def start(self):
        try:
            self._run_player()
        except (KeyboardInterrupt, PlayerExitException):
            self.close()
            self.vlc_media_player.stop()
            print('Good bye')
        finally:
            return True

    def get_tracks(self):
        # This method returns list of tracks
        raise NotImplementedError

    def _run_player(self):

        while True:
            tracks = self.get_tracks()
            i = 0
            while True:
                try:
                    track_id = choose_track_id(tracks[i])
                except KeyError:
                    i += 1
                    continue

                cmd = self._play_track(track_id)

                if cmd == 'f':
                    i += 1
                    if i >= len(tracks):
                        i = 0
                elif cmd == 'b':
                    i -= 1
                    if i < 0:
                        i = len(tracks) - 1
                elif cmd == 's':
                    break

    def _play_track(self, track_id):
        self.prepare()
        try:
            info = self.api.get_track_info(track_id)
        except CallFailure:
            info = None

        try:
            url = self.api.get_stream_url(track_id)
        except CallFailure as e:
            warnings.warn(str(e))
            return 'f'

        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(urllib.request.urlopen(url).read())

        self.vlc_media_player.set_mrl(tmp.name)
        self.vlc_media_player.play()

        paused = False
        duration = int(info['durationMillis'])

        while True:
            clear_screen()
            print_track_info(info)

            current = self.vlc_media_player.get_time()
            remain = (duration - current) / 1000
            timeout = min(remain, self.interval)

            print_bar(current, duration, remain, self.width)
            print_command_list()

            if paused:
                cmd = input('PAUSED\n>>')
            else:
                try:
                    cmd = inputimeout(timeout=timeout, prompt='>>')
                except TimeoutOccurred:
                    if remain > self.interval:
                        continue
                    cmd = 'f'

            if is_next(cmd):
                self.vlc_media_player.stop()
                tmp.close()
                return cmd
            elif is_quit(cmd):
                tmp.close()
                raise PlayerExitException
            elif cmd == 'p':
                paused = not paused
                self.vlc_media_player.pause()
