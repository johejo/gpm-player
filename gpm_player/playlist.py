import argparse
import getpass

from .__version__ import __version__
from .exceptions import PlayerExitException
from .common import BasePlayer, is_digit, is_quit


class PlayListPlayer(BasePlayer):
    def __init__(self, *, email=None, password=None, interval=3, width=50):
        super().__init__(email=email, password=password, interval=interval,
                         width=width)

    def get_tracks(self):
        self.prepare()
        playlists = self.api.get_all_user_playlist_contents()

        for i, playlist in enumerate(playlists):
            print('{}: {}'.format(i, playlist['name']))

        while True:
            cmd = input('\nSelect PlayList (Input Number)\n>>')
            if is_quit(cmd):
                raise PlayerExitException
            elif is_digit(cmd, len(playlists) - 1):
                n = int(cmd)
                tracks = playlists[n]['tracks']
                break

        return tracks


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

    try:
        email = input('Email: ')
        password = getpass.getpass()
    except KeyboardInterrupt:
        return

    player = PlayListPlayer(email=email, password=password,
                            interval=arg.interval, width=arg.width)
    player.start()
