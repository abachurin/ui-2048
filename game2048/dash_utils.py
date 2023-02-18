from dash import no_update as NUP
from dash import dcc, html, callback_context
from dash.dependencies import ClientsideFunction
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, MultiplexerTransform, Output, Input, State
from dash_extensions import EventListener

from .game_mechanics import *

navbar_logo = './assets/favicon.ico'
navbar_title = 'Robot 2048'

modals_draggable = ['login', 'files', 'users', 'agent', 'game_option']
modals_open_close = ['login', 'files', 'users']
modals_just_close = ['agent', 'game_option']
buttons_to_confirm = {
    'del_user_open': 'confirm_delete',
    'users_delete': 'confirm_user_delete'
}

mode_names = {
    'guide': 'HELP!',
    'train': 'Train Agent',
    'test': 'Collect Agent Statistics',
    'watch': 'Watch Agent Play',
    'replay': 'Replay Game',
    'play': 'Play Yourself'
}
mode_list = list(mode_names) + ['files', 'del_user'] + ['users']
keyboard_dict = {
    'Left': 0,
    'Up': 1,
    'Right': 2,
    'Down': 3
}
self_play_instruction = 'When two equal tiles collide, they combine to make one tile that displays their sum. ' \
                        'as the game progresses, the tiles reach higher and the board gets more crowded. ' \
                        'The objective is to reach highest possible score before the board fills up.\n' \
                        '-----------------------------------------\nUse buttons below or keyboard. Good luck!'

AGENT_PARAMS = {
    'train': {
        'agent_ex': {'element': 'select', 'value': None, 'options': []},
        'agent_new': {'element': 'input', 'type': 'text', 'value': None},
        'n': {'element': 'select', 'value': 4, 'options': [2, 3, 4, 5, 6], 'disabled': True},
        'alpha': {'element': 'input', 'type': 'number', 'value': 0.25, 'step': 0.0001, 'disabled': True},
        'decay': {'element': 'input', 'type': 'number', 'value': 0.75, 'step': 0.01, 'disabled': True},
        'step': {'element': 'input', 'type': 'number', 'value': 10000, 'step': 1000, 'disabled': True},
        'min_alpha': {'element': 'input', 'type': 'number', 'value': 0.01, 'step': 0.0001},
        'episodes': {'element': 'input', 'type': 'number', 'value': 10000, 'step': 1000, 'max': 100000},
    },
    'test': {
        'agent': {'element': 'select', 'value': None, 'options': []},
        'depth': {'element': 'input', 'type': 'number', 'value': 0, 'step': 1, 'min': 0, 'max': 4},
        'width': {'element': 'input', 'type': 'number', 'value': 1, 'step': 1, 'min': 1, 'max': 4},
        'trigger': {'element': 'input', 'type': 'number', 'value': 0, 'step': 1, 'min': 0, 'max': 8},
        'episodes': {'element': 'input', 'type': 'number', 'value': 100, 'step': 100, 'min': 100, 'max': 1000}
    }
}
AGENT_TRAIN_LIST = list(AGENT_PARAMS['train'])[2:]
AGENT_TRAIN_DEF = {v: AGENT_PARAMS['train'][v]['value'] for v in AGENT_TRAIN_LIST}
AGENT_TEST_LIST = list(AGENT_PARAMS['train'])[1:]


def core_id(v):
    return v[v.find('p') + 2:]


def opt_list(values):
    return [{'label': v, 'value': v} for v in values]


def params_line(mode, p):
    data = AGENT_PARAMS[mode][p]
    element = data['element']
    del data['element']
    header = 'Agent' if 'agent' in p else p[0].upper() + p[1:]
    data['id'] = f'{mode}_p_{p}'
    data['className'] = 'no-border'
    if mode == 'train':
        data['value'] = None
    if 'options' in data:
        data['options'] = opt_list(data['options'])
    choice_div = dbc.Input(**data) if element == 'input' else dbc.Select(**data)
    return dbc.InputGroup([dbc.InputGroupText(header, className='app-par-text'), choice_div], style={'margin': '0.1rem'})


def download_from_url(url: str):
    name = url.split('/')[-1].split('?')[0]
    r = requests.get(url, stream=True)
    if r.ok:
        with open(name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
        to_send = dcc.send_file(name)
        os.remove(name)
        return Resp.GOOD, to_send
    else:
        return f'Download failed: {r.status_code}, {r.text}', None


def general_alert(text, good=False):
    if not text:
        return NUP
    color = 'success' if good else 'warning'
    duration = 3000 if good else 10000
    return [dbc.Alert(text, dismissable=True, fade=True, color=color, duration=duration)]


def is_bad_name(s):
    return s is None or not re.match("^[\w\d_]+$", s)


def display_agent_window(params):
    return [
        html.Div(f'Working: {params["idx"]}')
    ]


def while_loading(idx, top):
    return dcc.Loading(id=idx, type='cube', color='var(--bs-blue)', className='loader', style={'top': f'{top}rem'})


cell_size = 7
x_position = {i: f'{i * cell_size}rem' for i in range(4)}
y_position = {i: f'{i * cell_size + 3}rem' for i in range(4)}


def display_game(game):
    header = f'Score = {game["score"]}, moves = {game["moves"]}'
    move = game['next_move']
    match move:
        case None:
            pass
        case -1:
            header += ' ... Game over!'
        case _:
            header += f'Next move = {GAME.actions[move]}'
    return dbc.Card(children=[html.Div(header, className='app-game-header')] + [
            html.Div(GAME.tiles[game['row'][j][i]], className='app-game-cell',
                     style={'left': x_position[i], 'top': y_position[j],
                            'background': f'var(--app-color-{game["row"][j][i]})'})
            for j in range(4) for i in range(4)], style={'width': '28rem'})


EMPTY_GAME = GAME.empty_game()
EMPTY_BOARD = display_game(EMPTY_GAME)
