import vlc
from gmusicapi import Mobileclient
from getpass import getpass
import requests
import time
from inputimeout import inputimeout, TimeoutOccurred


def ask_for_credentials():
    api = Mobileclient()

    logged_in = False
    attempts = 0

    while not logged_in and attempts < 3:
        email = input('Email: ')
        password = getpass()

        logged_in = api.login(email, password, Mobileclient.FROM_MAC_ADDRESS)

        attempts += 1

    return api


def main():
    api = ask_for_credentials()

    if not api.is_authenticated():
        print('Sorry, those credentials weren\'t accepted.')
        return

    print('Successfully logged in.\n')

    while True:
        stations, n = select_station(api)
        if n == len(stations):
            target = 'IFL'

        else:
            target = stations[n]['id']

        tracks = api.get_station_tracks(target)

        i = 0
        while i < len(tracks):
            try:
                track_id = tracks[i]['storeId']
            except KeyError:
                i += 1
                continue

            cmd = play(api, track_id)
            if cmd == 'f':
                i += 1
            elif cmd == 'b':
                i -= 1
            if cmd == 's' or i < 0:
                break


def select_station(api):
    stations = api.get_all_stations()
    i = 0
    for station in stations:
        print(i, station['name'])
        i += 1

    print(i, 'I`m Feeling Lucky')

    while True:
        n = input('\nSelect station. (Input number.)\n>>')
        if n == 'q':
            exit()
        if n.isdigit():
            selected = int(n)
            if 0 <= selected <= len(stations):
                break

    return stations, selected


def play(api, track_id):
    try:
        stream_url = api.get_stream_url(track_id)
    except:
        return 'f'

    content = requests.get(url=stream_url).content
    with open('cache.mp3', 'wb') as f:
        f.write(content)

    is_paused = False
    p = vlc.MediaPlayer('cache.mp3')
    p.play()
    begin_time = time.monotonic()
    track_duration = int(api.get_track_info(track_id)['durationMillis']) // 1000
    pause_begin = pause_durations = 0

    while True:
        music_simple_info(api, track_id)

        print(
            '\n'
            'Command List\n'
            '\'q\' stop and quit\n'
            '\'p\' pause or play\n'
            '\'f\' go to next track\n'
            '\'b\' back to previous track\n'
            '\'r\' restart current track\n'
            '\'s\' back to station menu\n'
        )

        timeout = track_duration - (time.monotonic() - begin_time) + pause_durations

        if is_paused:
            print('PAUSED')
            cmd = input('>>')
        else:
            try:
                cmd = inputimeout(timeout=timeout, prompt='>>')
            except TimeoutOccurred:
                cmd = 'f'

        if cmd == 'q':
            p.stop()
            api.logout()
            print('\nAll done!\n')
            exit()

        elif cmd == 'p':
            p.pause()
            is_paused = not is_paused
            if is_paused:
                pause_begin = time.monotonic()
            else:
                pause_end = time.monotonic()
                pause_durations += pause_end - pause_begin

        elif cmd == 'f' or cmd == 'b' or cmd == 'r' or cmd == 's':
            p.stop()
            break

    return cmd


def get_track_hits_id(results):
    return results['track_hits'][0]['track']['storeId']


def music_simple_info(api, track_id):
    info = api.get_track_info(track_id)
    length = int(info['durationMillis'])
    print()
    print('Title: {}'.format(info['title']))
    print('Album: {}'.format(info['album']))
    print('Artist: {}'.format(info['artist']))
    print('Length: {0}m{1}s'.format(length // 1000 // 60, length // 1000 % 60))


if __name__ == '__main__':
    main()
