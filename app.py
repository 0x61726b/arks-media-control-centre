import logging
import os
import datetime
import click
import config
from flask import Flask, request, send_from_directory, abort, jsonify
import win32api
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# Define Flask App
import requests
from lastfm import get_user_recent_tracks
import datetime

app = Flask(__name__)
app.url_map.strict_slashes = False

def configure_logging():
    logging.basicConfig(level=logging.INFO)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(current_dir, "logs")
    handler = logging.FileHandler(filename='{}/{}.log'.format(logs_dir, datetime.datetime.now().strftime('%Y-%m-%d')),
                                  encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    logger = logging.getLogger()
    logger.addHandler(handler)

@app.before_request
def clear_trailing():
    from flask import redirect, request

    rp = request.path
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route('/pc/', methods=['GET'])
def pc():
    action = request.args.get('action')
    if action == 'shutdown':
        #os.system('shutdown /s /t 1')
        return jsonify(dict(result=1))

    return "anan"

def get_np_from_mpc():
    mpc_web_r = requests.get('http://localhost:13579/info.html')
    video_file_start = mpc_web_r.text.index('&bull;')
    video_file_end   = mpc_web_r.text.index('&bull;', video_file_start+1)
    video_file = mpc_web_r.text[video_file_start + len('&bull;'):(video_file_end)].strip()

    time_end = mpc_web_r.text.index('&bull;', video_file_end+1)
    time = mpc_web_r.text[video_file_end + len('&bull;'):time_end].strip()

    time_current = time.split('/')[0]
    time_total = time.split('/')[1]

    return dict(video_file=video_file, time_current=time_current, time_total=time_total, image="/test.jpg")

def get_np_from_lastfm():
    tracks = get_user_recent_tracks('arkenthera', 1)
    if tracks[0].is_nowplaying:
        return tracks[0]
    return None

@app.route('/<filename>')
def static_subdir(filename=None):
    try:
        file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name += '.jpg'
        # if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), "snapshots", file_name)):
        #     return send_from_directory(os.path.join(os.path.dirname(os.path.realpath(__file__)), "snapshots"),
        #                                file_name)

        r = requests.get("http://localhost:13579/snapshot.jpg")
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'snapshots', file_name), 'wb') as f:
            f.write(r.content)
            return send_from_directory(os.path.join(os.path.dirname(os.path.realpath(__file__)), "snapshots"), file_name)
    except Exception as ex:
        return send_from_directory("",'test.jpg')

@app.route('/status/', methods=['GET'])
def status():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_volume = volume.GetMasterVolumeLevelScalar() * 100
    mute_state = volume.GetMute()
    mpc = None
    try:
        mpc = get_np_from_mpc()
    except:
        pass

    np_lastfm = None
    try:
        np_lastfm = get_np_from_lastfm()
        np_lastfm = dict(track_title = np_lastfm.track.title, artist_name = np_lastfm.track.artist.name, track_image = np_lastfm.track.image)
    except:
        pass
    return jsonify(dict(volume=int(current_volume),mute=bool(mute_state), mpc=mpc, music=np_lastfm))

@app.route('/media/', methods=['GET'])
def media():
    action = request.args.get('action')
    valid_actions = ['playpause', 'next', 'previous', 'volume', 'mute']
    if not action in valid_actions:
        return jsonify(dict(result=0))

    if action == 'playpause':
        hwcode = win32api.MapVirtualKey(0xB3, 0) # 0xB3 = VK_MEDIA_PLAY_PAUSE
        win32api.keybd_event(0xB3, hwcode)
        return jsonify(dict(result=1))

    if action == 'next':
        hwcode = win32api.MapVirtualKey(0xB0, 0)  # 0xB3 = VK_MEDIA_NEXT_TRACK
        win32api.keybd_event(0xB0, hwcode)
        return jsonify(dict(result=1))

    if action == 'previous':
        hwcode = win32api.MapVirtualKey(0xB1, 0)  # 0xB3 = VK_MEDIA_PREV_TRACK
        win32api.keybd_event(0xB1, hwcode)
        return jsonify(dict(result=1))

    if action == 'volume':
        value = request.args.get('value')
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevelScalar()*100
        print(current_volume)
        volume.SetMasterVolumeLevelScalar(int(value)/100, None)
        return jsonify(dict(result=1))

    if action == 'mute':
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1 if not volume.GetMute() else 0, None)
        return jsonify(dict(result=1))

    return jsonify(dict(result=0))


@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        while True:
            configure_logging()
            app.run(host='0.0.0.0', port=config.PORT)
            print("Restarting...")

if __name__ == '__main__':
    main()