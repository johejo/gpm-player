from .exceptions import PlayerExitException
from .common import BasePlayer, is_digit, is_quit, run


class StationPlayer(BasePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_tracks(self):
        self.prepare()
        stations = self.api.get_all_stations()
        print()

        for i, station in enumerate(stations):
            print('{}: {}'.format(i, station['name']))

        print('{}: {}'.format(len(stations), 'I`m Feeling Lucky'))

        while True:
            cmd = input('\nSelect Station (Input Number)\n>>')
            if is_quit(cmd):
                raise PlayerExitException
            elif is_digit(cmd, len(stations)):
                n = int(cmd)
                if n == len(stations):
                    station_id = 'IFL'
                else:
                    station_id = stations[n]['id']
                break

        tracks = self.api.get_station_tracks(station_id)
        return tracks


def main():
    run(StationPlayer)
