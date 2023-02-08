from datetime import datetime, timedelta
import numpy as np
import time
import sys
from pprint import pprint
import random
import pickle
import json
from collections import deque
import os
import time
import boto3
import base64
from multiprocessing import Process
from threading import Thread
# import psutil
from dateutil import parser
import requests
from enum import Enum

import dash
from dash import no_update as NUP
from dash import dcc, html
from dash.dependencies import ClientsideFunction
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, MultiplexerTransform, Output, Input, State
from dash_extensions import EventListener
import plotly.express as px

working_directory = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(working_directory, 'config.json'), 'r') as f:
    CONF = json.load(f)
LOCAL = os.environ.get('S3_URL', 'local') == 'local'
dash_intervals = CONF['intervals']
dash_intervals['refresh'] = dash_intervals['refresh_sec'] * 1000
dash_intervals['check_run'] = dash_intervals['refresh_sec'] * 2
dash_intervals['vc'] = dash_intervals['vc_sec'] * 1000
dash_intervals['next'] = dash_intervals['refresh_sec'] + 180
LOWEST_SPEED = 50

BACK_URL = 'http://localhost:5000' if LOCAL else 'http://api:5000'


class Resp(Enum):
    NONE = 1
    INVALID = 2
    BAD = 3
    GOOD = 4


def api_request(kind, suffix, body):
    url = f'{BACK_URL}/{suffix}'
    try:
        response = requests.request(kind, url, json=body)
        if response.status_code != 200:
            return {'status': Resp.INVALID, 'msg': f'Invalid backend response: {response.status_code}'}
        response_message = json.loads(response.text)
        if response_message['status'] != 'ok':
            return {'status': Resp.BAD, 'msg': response_message['status']}
        else:
            return {'status': Resp.GOOD, 'msg': response_message['msg']}
    except requests.exceptions.ConnectionError:
        return {'status': Resp.NONE, 'msg': 'No connection to backend, contact Support'}


def time_suffix(precision=1):
    return ''.join([v for v in str(datetime.utcnow()) if v.isnumeric()])[4:-precision]


def next_time():
    return str(datetime.utcnow() + timedelta(seconds=dash_intervals['next']))


def temp_local_name(name):
    body, ext = name.split('.')
    return f'temp{time_suffix()}.{ext}', ext


navbar_logo = './assets/favicon.ico'
navbar_title = 'Robot 2048'

# Some necessary variables and useful functions
mode_names = {
    'guide': 'HELP!',
    'train': 'Train Agent',
    'stat': 'Collect Agent Statistics',
    'watch': 'Watch Agent Play',
    'replay': 'Replay Game',
    'play': 'Play Yourself'
}
mode_list = list(mode_names) + ['files', 'del_user']
act_list = {
    'download': 'Download',
    'upload': 'Upload',
    'delete': 'Delete'
}
modals_draggable = ['login']
modals_open_close = ['login']

params_list = ['name', 'n', 'alpha', 'decay', 'decay_step', 'low_alpha_limit', 'Training episodes']
params_dict = {
    'name': {'element': 'input', 'type': 'text', 'value': 'test_agent', 'disable': False},
    'n': {'element': 'select', 'value': 4, 'options': [2, 3, 4, 5, 6], 'disable': True},
    'alpha': {'element': 'input', 'type': 'number', 'value': 0.25, 'step': 0.0001, 'disable': False},
    'decay': {'element': 'input', 'type': 'number', 'value': 0.75, 'step': 0.01, 'disable': False},
    'decay_step': {'element': 'input', 'type': 'number', 'value': 10000, 'step': 1000, 'disable': False},
    'low_alpha_limit': {'element': 'input', 'type': 'number', 'value': 0.01, 'step': 0.0001, 'disable': False},
    'Training episodes': {'element': 'input', 'type': 'number', 'value': 100000, 'step': 1000, 'disable': False},
}
keyboard_dict = {
    'Left': 0,
    'Up': 1,
    'Right': 2,
    'Down': 3
}
cell_size = CONF['cell_size']
x_position = {i: f'{i * cell_size}px' for i in range(4)}
y_position = {i: f'{i * cell_size + 35}px' for i in range(4)}
numbers = {i: str(1 << i) if i else '' for i in range(16)}
colors = CONF['colors']
colors = {int(v): colors[v] for v in colors}


def general_alert(text, good=False):
    if not text:
        return NUP
    color = 'success' if good else 'warning'
    return [dbc.Alert(text, dismissable=True, fade=True, color=color, duration=5000)]
