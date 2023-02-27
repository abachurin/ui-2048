from datetime import datetime
from pprint import pprint, pformat
import random
import json
import re
import os
import requests
from enum import Enum

LOCAL = os.environ.get('S3_URL', 'local') == 'local'
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
            return Resp.INVALID, f'Invalid backend response: {response.status_code}'
        response_message = json.loads(response.text)
        if response_message['status'] != 'ok':
            return Resp.BAD, response_message['status']
        else:
            return Resp.GOOD, response_message['content']
    except requests.exceptions.ConnectionError:
        return Resp.NONE, 'No connection to backend, contact Support'


def time_suffix():
    return str(datetime.now())[-6:]


def time_now():
    return str(datetime.now())[:19]
