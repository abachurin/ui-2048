from dash import no_update as NUP
from dash import dcc, html, callback_context
from dash.dependencies import ClientsideFunction
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, MultiplexerTransform, Output, Input, State
from dash_extensions import EventListener
from dash.long_callback import DiskcacheLongCallbackManager
import diskcache

from .game_mechanics import *

with open('base/config.json', 'r') as f:
    config = json.load(f)
    FIELDS = config['fields']
    MAX_JOBS = config['max_jobs']
    SPEED = config['replay_speed']
    self_play_instruction = config['self_play_instruction']
    job_description_header = config['job_description_header']


navbar_logo = './assets/favicon.ico'
navbar_title = 'Robot 2048'

divs_draggable = ['login', 'files', 'users', 'agent', 'game', 'chart']
divs_only_one_open = ['login', 'files', 'users', 'agent', 'game']
divs_open_close = ['login', 'files', 'users', 'chart']
divs_just_close = ['agent', 'game']
buttons_to_confirm = {
    'del_user_open': 'confirm_delete',
    'users_delete': 'confirm_user_delete'
}
modal_open_close = ['guide']

mode_names = {
    'guide': 'HELP!',
    'train': 'Train Agent',
    'test': 'Agent Statistics',
    'watch': 'Watch Agent Play',
    'replay': 'Replay Game',
    'play': 'Play Yourself'
}
mode_names_disabled = ['train', 'test', 'files', 'del_user', 'users']
keyboard_dict = {
    'Left': 0,
    'Up': 1,
    'Right': 2,
    'Down': 3
}
job_status_description = {
    -1: 'KILL',
    0: 'STOP',
    1: 'IN QUEUE',
    2: 'WORKING'
}

AGENT_PARAMS = {
    'train': {
        'agent_ex': {'element': 'select', 'value': None, 'options': []},
        'agent_new': {'element': 'input', 'type': 'text', 'value': None},
        'n': {'element': 'select', 'value': 4, 'options': [2, 3, 4, 5, 6], 'disabled': True},
        'alpha': {'element': 'input', 'type': 'number', 'value': 0.2, 'step': 0.0001},
        'decay': {'element': 'input', 'type': 'number', 'value': 0.75, 'step': 0.01},
        'step': {'element': 'input', 'type': 'number', 'value': 10000, 'step': 1000},
        'min_alpha': {'element': 'input', 'type': 'number', 'value': 0.01, 'step': 0.0001},
        'episodes': {'element': 'input', 'type': 'number', 'value': 10000, 'step': 1000, 'max': 100000},
    },
    'test': {
        'agent': {'element': 'select', 'value': None, 'options': []},
        'depth': {'element': 'input', 'type': 'number', 'value': 0, 'step': 1, 'min': 0, 'max': 4},
        'width': {'element': 'input', 'type': 'number', 'value': 1, 'step': 1, 'min': 1, 'max': 4},
        'trigger': {'element': 'input', 'type': 'number', 'value': 0, 'step': 1, 'min': 0, 'max': 8},
        'episodes': {'element': 'input', 'type': 'number', 'value': 100, 'step': 100, 'min': 100, 'max': 1000}
    },
    'watch': {
        'agent': {'element': 'select', 'value': None, 'options': []},
        'depth': {'element': 'input', 'type': 'number', 'value': 0, 'step': 1, 'min': 0, 'max': 4},
        'width': {'element': 'input', 'type': 'number', 'value': 1, 'step': 1, 'min': 1, 'max': 4},
        'trigger': {'element': 'input', 'type': 'number', 'value': 0, 'step': 1, 'min': 0, 'max': 8},
    }
}
AGENT_TRAIN_LIST = list(AGENT_PARAMS['train'])[2:]
AGENT_TRAIN_DEF = {v: AGENT_PARAMS['train'][v]['value'] for v in AGENT_TRAIN_LIST}
AGENT_TEST_LIST = list(AGENT_PARAMS['test'])[1:]


def core_id(v):
    return v[v.find('p') + 2:]


def opt_list(values):
    if not values:
        return []
    if isinstance(values[0], dict):
        return [{'label': v['idx'], 'value': v['idx']} for v in values]
    else:
        return [{'label': v, 'value': v} for v in values]


def agents_extra(agents: list):
    opts = [v['idx'] for v in agents] + ['Random moves', 'Best score moves']
    return opt_list(opts)


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
    return dbc.InputGroup([dbc.InputGroupText(header, className='app-par-text'), choice_div],
                          style={'margin': '0.1rem'})


def job_description(job: dict):
    mode = job['mode']
    header = f"{job['agent']}\n"
    des_list = AGENT_TRAIN_LIST if mode == 'train' else AGENT_TEST_LIST
    return job_description_header[mode], header + \
        '\n'.join([str(job[v]) for v in des_list]) + '\n' + job['launch_time']


def get_from_url(url: str, mode='to_send'):
    name = url.split('/')[-1].split('?')[0]
    r = requests.get(url, stream=True)
    if r.ok:
        with open(name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
        if mode == 'to_send':
            result = dcc.send_file(name)
        else:
            # mode = 'local'
            with open(name, 'rb') as f:
                result = pickle.load(f)
        os.remove(name)
        return Resp.GOOD, result
    else:
        return f'Download failed: {r.status_code}, {r.text}', None


def get_array_item(user: dict, kind: str, idx: str):
    try:
        return next(v for v in user[kind] if v['idx'] == idx)
    except StopIteration:
        return


def download_json(user: dict, kind: str, idx: str):
    item = get_array_item(user, kind, idx)
    if item is None:
        return NUP
    filename = f"{idx.replace(':', '_')}.json"
    with open(filename, 'w') as f:
        json.dump(item, f)
    to_send = dcc.send_file(filename)
    os.remove(filename)
    return to_send


def description_for_file_manager(user: dict, kind: str, idx: str):
    item = get_array_item(user, kind, idx)
    if item is None:
        return None
    match kind:
        case 'Agents':
            return f"Creator = {item['creator']}\n" \
                   f"Agent signature N = {item['n']}\n" \
                   f"Current Learning Rate = {item['alpha']}\n" \
                   f"LR decay = {item['decay']}\n" \
                   f"Decay step = {item['step']}\n" \
                   f"LR floor = {item['min_alpha']}\n" \
                   f"Trained for episodes = {item['train_eps']}\n" \
                   f"Best score so far = {item['best_score']}\n" \
                   f"Maximum tile achieved = {1 << item['max_tile']}"
        case 'Games':
            return f"Player = {item['player']}\n" \
                   f"Score = {item['score']}\n" \
                   f"Number of moves = {item['num_of_moves']}\n" \
                   f"Maximum tile achieved = {item['max_tile']}"
        case 'Jobs':
            return f"Status = {job_status_description[item['status']]}\n" \
                   f"User = {item['name']}\n" \
                   f"Created at = {item['creation_time']}\n" \
                   f"Launched at = {item['launch_time']}\n" \
                   f"Agent = {item['agent']}\n" \
                   f"Mode = {item['mode'].upper()}"


def general_alert(text: str, good=False):
    if not text:
        return NUP
    color = 'success' if good else 'warning'
    duration = 3000 if good else 10000
    return [dbc.Alert(text, dismissable=True, fade=True, color=color, duration=duration)]


def is_bad_name(s: str):
    return (s is None) or (not re.match("^[\w\d_]+$", s)) or (len(s) > 12) or (s in ('Random', 'Score'))


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
            header += f', Next move = {GAME.actions[move].upper()}'
    return dbc.Card(children=[html.Div(header, className='app-game-header')] + [
            html.Div(GAME.tiles[game['row'][j][i]],
                     className='app-game-cell blink-me' if [j, i] == game['last_tile'] else 'app-game-cell',
                     style={'left': x_position[i], 'top': y_position[j],
                            'background': f'var(--app-color-{game["row"][j][i]})'})
            for j in range(4) for i in range(4)], style={'width': '28rem'})


EMPTY_GAME = GAME.empty_game()
EMPTY_BOARD = display_game(EMPTY_GAME)
