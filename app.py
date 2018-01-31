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

app = Flask(__name__)

def configure_logging():
    logging.basicConfig(level=logging.INFO)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(current_dir, "logs")
    handler = logging.FileHandler(filename='{}/{}.log'.format(logs_dir, datetime.datetime.now().strftime('%Y-%m-%d')),
                                  encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    logger = logging.getLogger()
    logger.addHandler(handler)

@app.route('/pc/', methods=['GET'])
def pc():
    action = request.args.get('action')
    if action == 'shutdown':
        os.system('shutdown /s /t 1')
        return jsonify(dict(result=0))

@app.route('/status/', methods=['GET'])
def status():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_volume = volume.GetMasterVolumeLevelScalar() * 100
    mute_state = volume.GetMute()
    return jsonify(dict(volume=int(current_volume),mute=bool(mute_state)))

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