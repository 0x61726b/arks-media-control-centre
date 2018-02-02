import logging
import json
import requests
import datetime
import urllib.parse

API_KEY = "1c15b9ea24af56c25eac1d40b24cf6b5"
API_SECRET = "2fc65d3ac585f3738b8c56a8b6013d6f"
BASE_URL = f"http://ws.audioscrobbler.com/2.0/?&api_key={API_KEY}&format=json&"

class LastfmArtist:
    def __init__(self, name, url, play_count, image, listeners, tags = [], bio = None,similar_artists=[]):
        self.name = name
        self.url = url
        self.play_count = play_count
        self.image = image
        self.listeners = listeners
        self.similar_artists = similar_artists
        self.tags = tags
        self.bio = bio

class LastfmAlbum:
    def __init__(self, name, play_count, url, artist, image, tracks, listeners = 0):
        self.name = name
        self.play_count = play_count
        self.url = url
        self.artist = artist
        self.image = image
        self.tracks = tracks
        self.listeners = listeners

class LastfmTrack:
    def __init__(self,title, artist,album, image):
        self.artist = artist
        self.album = album
        self.image = image
        self.title = title

class LastfmUserTrack:
    def __init__(self, track, is_nowplaying):
        self.track = track
        self.is_nowplaying = is_nowplaying

def parse_tracks(json, is_recent = True):
    try:
        error = None

        track_instances = []
        try:
            error = json['error']
        except:
            if is_recent:
                recent_tracks = json['recenttracks']
            else:
                recent_tracks = json['artisttracks']
            attr = recent_tracks['@attr']
            tracks_array = recent_tracks['track']

            for track in tracks_array:
                name = track['name']
                img_count = len(track['image'])
                image = None
                try:
                    image = track['image'][3]['#text']
                except:
                    for i in range(img_count):
                        image = track['image'][i]

                album_inst = None
                artist_inst = None

                # Artist
                try:
                    artist = track['artist']
                    artist_name = artist['#text']
                    artist_inst = LastfmArtist(artist_name, None, 0, None, 0, [], None, [])
                except:
                    pass

                # Album
                try:
                    album = track['album']
                    album_text = album['#text']
                    album_inst = LastfmAlbum(album_text, 0, None, artist_inst, None, [])
                except:
                    pass

                is_nowplaying = False
                try:
                    track_attr = track['@attr']
                    if track_attr["nowplaying"] == "true":
                        is_nowplaying = True
                except:
                    pass

                if is_recent:
                    track_inst = LastfmTrack(name, artist_inst, album_inst, image)
                    track_inst = LastfmUserTrack(track_inst, is_nowplaying)
                else:
                    track_inst = LastfmTrack(name, artist_inst, album_inst, image)
                track_instances.append(track_inst)
        return track_instances
    except Exception as ex:
        return []

def get_user_recent_tracks(user_name, limit=None, fetch_all=False, time_from = None, time_to = None):
    if limit == None:
        limit = 1000

    tracks = []
    request_url = f"{BASE_URL}method=user.getRecentTracks&user={user_name}&limit={limit}"
    if not time_from == None and not time_to == None:
        request_url = f"{request_url}&from={time_from}&to={time_to}"


    try:
        request_result = requests.get(request_url)

        if request_result.status_code == 200:
            parsed_json = json.loads(request_result.text)
            try:
                error = parsed_json['error']
            except:
                recent_tracks = parsed_json['recenttracks']
                attr = recent_tracks['@attr']
                current_page = int(attr['page'])
                total_pages = int(attr['totalPages'])
                total_tracks = int(attr['total'])

                # Parse this page
                tracks = parse_tracks(parsed_json)

                if fetch_all:  # Note that, in our app, we wont currently need recent tracks more than 1000, so its safe to do this
                    for i in range(total_pages + 1):
                        if i == 1 or i == 0:
                            continue
                        page_tracks = []
                        page_request = requests.get(f'{request_url}&page={i}')
                        if page_request.status_code == 200:
                            page_content = page_request.text
                            page_json = json.loads(page_content)
                            page_tracks = parse_tracks(page_json)

                        for page_track in page_tracks:
                            tracks.append(page_track)
    except:
        pass

    return tracks