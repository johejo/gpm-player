import platform
import subprocess
import tempfile
import warnings
import argparse
import getpass

import requests
import vlc
from gmusicapi import Mobileclient
from inputimeout import inputimeout, TimeoutOccurred

from .__version__ import __version__
from .exceptions import LoginFailure

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


class StationPlayer(object):
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

    def start_player(self):
        try:
            self._start_player()
        except KeyboardInterrupt:
            self.close()

        return True

    def _start_player(self):

        if not self._logged_in:
            msg = 'Login is not completed.'
            warnings.warn(msg)

        if not self.api.is_authenticated():
            raise LoginFailure

        while True:
            cmd = self._select_station()

            if is_quit(cmd):
                return True
            elif is_digit(cmd, len(self.stations)):
                n = int(cmd)
            else:
                raise RuntimeError

            if n == len(self.stations):
                target = 'IFL'
            else:
                target = self.stations[n]['id']

            tracks = self.api.get_station_tracks(target)

            i = 0
            while True:
                try:
                    track_id = tracks[i]['storeId']
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
                elif is_quit(cmd):
                    return True

    def _select_station(self):
        self.stations = self.api.get_all_stations()

        for i, station in enumerate(self.stations):
            print('{}: {}'.format(i, station['name']))

        print('{}: {}'.format(len(self.stations), 'I`m Feeling Lucky'))

        while True:
            cmd = input('\nSelect Station (Input Number)\n>>')
            if is_quit(cmd) or is_digit(cmd, len(self.stations)):
                return cmd

    def _play_track(self, track_id):

        info = self.api.get_track_info(track_id)
        url = self.api.get_stream_url(track_id)

        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(requests.get(url).content)

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

            if is_quit(cmd) or is_next(cmd):
                self.vlc_media_player.stop()
                tmp.close()
                return cmd
            elif cmd == 'p':
                paused = not paused
                self.vlc_media_player.pause()


def set_args():
    p = argparse.ArgumentParser()
    p.add_argument('-v', '--version', action='version', version=__version__,
                   help='show version and exit')
    p.add_argument('-i', '--interval', nargs='?', default=3, type=float,
                   help='screen display update interval')
    p.add_argument('-w', '--width', nargs='?', default=50, type=int,
                   help='progress bar width')
    a = p.parse_args()
    return a


def main():
    arg = set_args()

    email = input('Email: ')
    password = getpass.getpass()

    player = StationPlayer(email=email, password=password,
                           interval=arg.interval, width=arg.width)
    player.start_player()
