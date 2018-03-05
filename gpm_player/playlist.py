from .exceptions import PlayerExitException
from .common import BasePlayer, is_digit, is_quit, run


class PlayListPlayer(BasePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_tracks(self):
        self.prepare()
        playlists = self.api.get_all_user_playlist_contents()
        print()

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


def main():
    run(PlayListPlayer)
