from game2048.dash_utils import *

dash_directory = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dash_directory, 'assets', 'user_guide.md'), 'r') as f:
    guide_interface = f.read()
with open(os.path.join(dash_directory, 'assets', 'structure.md'), 'r') as f:
    guide_structure = f.read()
guide_history = {}
for i in (1, 2, 3, 4):
    with open(os.path.join(dash_directory, 'assets', f'project_{i}.md'), 'r') as f:
        guide_history[i] = f.read()


app = DashProxy(__name__, suppress_callback_exceptions=True,
                transforms=[MultiplexerTransform()], title='RL Agent 2048', update_title=None,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])

app.layout = dbc.Container([
    dcc.Interval(id='api_update', interval=5000, n_intervals=1, disabled=True),
    dcc.Store(id='user_profile', storage_type='session', data=None),
    dcc.Store(id='logs', storage_type='session', data=[]),
    dcc.Store(id='max_logs', storage_type='session'),
    dcc.Store(id='current_game_mode', storage_type='session'),
    dcc.Store(id='current_game', storage_type='session'),
    dcc.Store(id='current_agent_mode', storage_type='session'),
    dcc.Store(id='show_instruction', storage_type='session', data=1),
    EventListener(id='keyboard'),
    dcc.Interval(id='move_delay', n_intervals=0, disabled=True),
    dcc.Download(id='download'),
    html.Div(id='alert'),
    dcc.ConfirmDialog(id='confirm_delete',
                      message='Are you sure? All Agents assigned to this user will be deleted'),
    dcc.ConfirmDialog(id='confirm_user_delete',
                      message='Are you sure? All Agents assigned to this user will be deleted'),
    dbc.NavbarSimple(
        children=[
            dbc.Button('Manage Users', id='users_open', className='app-btn', color='primary', disabled=True),
            dbc.Button('Manage Resources', id='files_open', className='app-btn app-r1', color='primary', disabled=True),
            dbc.Button('Delete Me', id='del_user_open', className='app-btn app-r1', disabled=True, color='primary'),
            dbc.Button('Log in', id='login_open', className='app-btn app-r1', color='success'),
            dbc.Button('Quit', id='quit', className='app-btn app-r1', color='warning')
        ],
        brand=dbc.Row([
            dbc.Col(html.Img(src=navbar_logo, height='25rem')),
            dbc.Col(dbc.NavbarBrand(navbar_title, className='ms-2'))
        ], align='center', className='g-0'),
        color='dark', dark=True, className='app-top-line'
    ),
    dbc.NavbarSimple(children=[
        dbc.NavLink(mode_names[v], id=f'{v}_open', disabled=True,
                    className='app-nav-item' + (' app-odd-item' if i % 2 else ''))
        for i, v in enumerate(list(mode_names))
        ], id='navbar', links_left=True, className='app-table-nav'),
    html.Div([
        dbc.ModalHeader('registration', close_button=False, id='login_header', className='app-modal-header'),
        dbc.ModalBody(children=[
            dbc.Input(id='login_name', className='app-input-field login-name', type='text', placeholder='User'),
            dbc.Input(id='login_pwd', className='app-input-field login-pwd', type='password', placeholder='Password'),
        ], className='app-modal-body'),
        dbc.ModalFooter([
            dbc.Button('Submit', id='login_submit', className='app-btn app-btn-submit', n_clicks=0, color='success'),
            dbc.Button('New', id='login_new', className='app-btn app-r1', n_clicks=0, color='primary'),
            dbc.Button('Quit', id='login_close', className='app-btn app-r1', n_clicks=0, color='warning')
        ], className='app-modal-footer')
    ], id='login', className='app-border', hidden=False),
    html.Div([
        dbc.ModalHeader('manage files', close_button=False, id='files_header', className='app-modal-header'),
        dbc.ModalBody(children=[
            html.Br(), html.Div('Agents/Games ?'),
            dcc.Dropdown(id='files_kind', options=opt_list(FIELDS), clearable=False),
            html.Br(), html.Div('Name:'),
            dcc.Dropdown(id='files_name'),
        ], className='app-modal-body'),
        dbc.ModalFooter([
            dbc.Button('Delete', id='files_delete', className='app-btn app-btn-submit', color='success'),
            dbc.Button('Download', id='files_download', className='app-btn app-r1', color='primary', disabled=False),
            dbc.Button('Quit', id='files_close', className='app-btn app-r1', color='warning')
        ], className='app-modal-footer')
    ], id='files', className='app-border', hidden=True),
    html.Div([
        dbc.ModalHeader('manage users', close_button=False, id='users_header', className='app-modal-header'),
        dbc.ModalBody(children=[
            html.Br(), html.Div('User :'),
            dcc.Dropdown(id='users_name', clearable=False),
            html.Br(), html.Div('Change Status'),
            dcc.Dropdown(id='users_change', clearable=False)
        ], className='app-modal-body'),
        dbc.ModalFooter([
            dbc.Button('Delete', id='users_delete', className='app-btn app-btn-submit', color='success'),
            dbc.Button('Set Status', id='users_status', className='app-btn app-r1', color='primary'),
            dbc.Button('Quit', id='users_close', className='app-btn app-r1', color='warning')
        ], className='app-modal-footer')
    ], id='users', className='app-border', hidden=True),
    dbc.Modal([
        dbc.ModalHeader([
                dbc.ButtonGroup([
                    dbc.Button('Interface', id='guide_ui', className='app-btn', color='info'),
                    dbc.Button('History', id='guide_pd', className='app-btn', color='primary'),
                    dbc.Button('Structure', id='guide_ps', className='app-btn', color='secondary'),
                ]),
                dbc.Button('Quit', id='guide_close', className='app-btn', color='warning')
            ],
            close_button=False, id='guide_header'),
        dbc.ModalBody(id='guide_body'),
    ], id='guide', size='xl', contentClassName='app-guide-body', className='app-border', scrollable=True),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Div([
                    dbc.ModalHeader(close_button=False, id='agent_header', className='app-modal-header'),
                    dbc.ModalBody(children=[
                        html.Div([
                            dbc.RadioItems(('Existing Agent', 'New Agent'), value='Existing Agent',
                                           inline=True, id='existing_new', className='app-train-radio'),
                            html.Div([
                                html.Div(params_line('train', 'agent_ex'), id='existing_visible', hidden=False),
                                html.Div(params_line('train', 'agent_new'), id='new_visible', hidden=True)]
                                     + [params_line('train', p) for p in AGENT_TRAIN_LIST
                                        ], className='app-train-box')
                        ], id='train_params', hidden=True),
                        html.Div([
                            params_line('test', p) for p in AGENT_PARAMS['test']
                        ], id='test_params', className='app-test-box', hidden=True)
                    ], className='app-modal-body'),
                    dbc.ModalFooter([
                        dbc.Button('Go!', id='agent_btn', className='app-btn app-btn-submit', color='success'),
                        dbc.Button('Quit', id='agent_close', className='app-btn app-r1', color='warning')
                    ], className='app-modal-footer')
                ], id='agent', className='app-border', hidden=True),
                html.Div('Waiting for action', id='what_agent', className='app-pane-header'),
                dbc.Row([
                    dbc.Col(html.Div(id='current_job_headers')),
                    dbc.Col(html.Div(id='current_job_values', className='app-job-values'), className='app-col-values'),
                    dbc.Col([
                        dbc.Button('Stop', id='stop_job', className='app-btn app-stop-job', color='info'),
                        dbc.Button('Kill', id='kill_job', className='app-btn app-kill-job', color='warning'),
                    ])
                ], className='app-agent-window'),
                html.Div(id='logs_window', className='app-logs-window'),
                dbc.Button('Clear logs', id='clear_logs', className='app-btn app-clear-logs', color='info'),
            ], className='app-pane align-items-center')
        ),
        dbc.Col(
            dbc.Card([
                dbc.Toast(self_play_instruction, header='Game instructions', headerClassName='inst-header',
                          id='instruction', className='app-border', dismissable=True, is_open=False),
                html.Div([
                    dbc.ModalHeader('Choose option', close_button=False, className='app-modal-header'),
                    dbc.ModalBody(children=[
                        html.Br(),
                        dcc.Dropdown(id='game_option_value', clearable=False),
                    ], className='app-modal-body'),
                    dbc.ModalFooter([
                        dbc.Button('Go!', id='go_game', className='app-btn app-btn-submit', color='success'),
                        dbc.Button('Quit', id='game_option_close', className='app-btn app-r1', color='warning')
                    ], className='app-modal-footer')
                ], id='game_option', className='app-border', hidden=True),
                html.Div('Waiting for action', id='what_game', className='app-pane-header'),
                dbc.CardBody(EMPTY_BOARD, id='game_board'),
                html.Div([
                    daq.Gauge(id='gauge', className='gauge',
                              color={"gradient": True, "ranges": {"blue": [0, 6], "yellow": [6, 8], "red": [8, 10]}}),
                    html.Div('DELAY', className='app-speed-header'),
                    dcc.Slider(id='gauge-slider', min=0, max=10, value=3, marks={v: str(v) for v in range(11)},
                               step=0.1, className='app-speed-slider'),
                    html.Div([
                        dbc.Button('PAUSE', id='pause_game', className='app-btn app-pause-btn', color='info'),
                        dbc.Button('RESUME', id='resume_game', className='app-btn app-resume-btn'),
                    ], className='app-button-line')
                ], id='gauge_group', className='app-gauge-group', hidden=False),
                html.Div([
                    dbc.Button('\u2190', id='move_0', className='move-button move-left'),
                    dbc.Button('\u2191', id='move_1', className='move-button move-up'),
                    dbc.Button('\u2192', id='move_2', className='move-button move-right'),
                    dbc.Button('\u2193', id='move_3', className='move-button move-down'),
                    dbc.Button('RESTART', id='restart_play', className='app-btn app-restart-btn', color='warning'),
                ], id='play-yourself-group', className='app-gauge-group', hidden=True),
            ], className='app-pane align-items-center'),
        )
    ])
], className='app-cont', fluid=True)


# general callbacks
for v in modals_open_close:
    @app.callback(
        Output(v, 'hidden'),
        Input(f'{v}_open', 'n_clicks'), Input(f'{v}_close', 'n_clicks')
    )
    def open_modal(*args):
        ctx = callback_context.triggered[0]
        if ctx['value'] is None:
            raise PreventUpdate
        trigger_id = ctx['prop_id'].split('.')[0][-1]
        return trigger_id == 'e'


for v in modals_just_close:
    @app.callback(
        Output(v, 'hidden'),
        Input(f'{v}_close', 'n_clicks')
    )
    def just_close(n):
        if n:
            return True
        raise PreventUpdate


for v in buttons_to_confirm:
    @app.callback(
        Output(buttons_to_confirm[v], 'displayed'),
        Input(v, 'n_clicks')
    )
    def display_confirm(n):
        if n:
            return True
        return False


#  Update User attributes and logs
@app.callback(
    Output('user_profile', 'data'), Output('logs', 'data'),
    Output('login_open', 'children'), Output('alert', 'children'),
    Input('api_update', 'n_intervals'), Input('clear_logs', 'n_clicks'),
    State('user_profile', 'data'), State('logs', 'data'), State('max_logs', 'data')
)
def api_update(n1, n2, user, logs, max_logs):
    ctx = callback_context
    if not ctx.triggered or not user:
        raise PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0]
    clear = action == 'clear_logs'
    name = user['name']
    body = {
        'name': name,
        'log_break': len(logs),
        'clear_logs': clear
    }
    resp, content = api_request('POST', 'update', body)
    if resp == Resp.GOOD:
        if clear:
            new_logs = content['new_logs']
        else:
            new_logs = (logs + content['new_logs'])[-max_logs:] if content['new_logs'] else NUP
        return content['profile'], new_logs, name, NUP
    elif resp == Resp.BAD:
        return None, [], 'Log in', general_alert(content)
    return NUP, NUP, NUP, general_alert(content)


@app.callback(
    Output('logs_window', 'children'),
    Input('logs', 'data')
)
def update_logs(logs):
    return '\n'.join(logs)


# Login
@app.callback(
    Output('login_open', 'children'), Output('login', 'hidden'), Output('user_profile', 'data'),
    Output('logs', 'data'), Output('alert', 'children'), Output('login_name', 'value'),
    Output('login_pwd', 'value'), Output('max_logs', 'data'),
    Input('login_submit', 'n_clicks'), Input('login_new', 'n_clicks'), Input('confirm_delete', 'submit_n_clicks'),
    State('login_name', 'value'), State('login_pwd', 'value'), State('user_profile', 'data')
)
def login_submit(n1, n2, n3, name, pwd, profile):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[1]
    if action == 'delete':
        name, pwd = profile['name'], 'x'
    if not name or not pwd:
        return NUP, NUP, NUP, NUP, general_alert('Name and Password should be filled'), NUP, NUP, NUP
    if is_bad_name(name):
        return NUP, NUP, NUP, NUP, general_alert('Name should only contain literals, numbers and "_" symbol'), \
               NUP, NUP, NUP
    body = {
        'name': name,
        'pwd': pwd,
        'action': action
    }
    resp, content = api_request('POST', 'user', body)
    if resp == Resp.GOOD:
        if action == 'delete':
            return 'Log in', False, None, [], general_alert(f'User {name} was successfully deleted', good=True), \
                   '', '', NUP
        user = content['profile']
        new_name = user['name']
        logs = user.pop('logs')
        msg = f'Welcome back, {new_name}!' if action == 'submit' else f'Welcome, {new_name}!'
        return new_name, True, user, logs, general_alert(msg, good=True), '', '', content['max_logs']
    else:
        return NUP, NUP, NUP, NUP, general_alert(content), NUP, NUP, NUP


@app.callback(
    [Output('train_p_n', 'options'), Output('train_p_agent_ex', 'options'),
     Output('current_job_headers', 'children'), Output('current_job_values', 'children'),
     Output('what_agent', 'children'), Output('api_update', 'disabled')] +
    [Output(f'{v}_open', 'disabled') for v in mode_list],
    Input('user_profile', 'data')
)
def display_name(user):
    if user:
        opts = [2, 3, 4, 5, 6] if user['status'] == 'admin' else [2, 3, 4]
        if not user['Jobs']:
            header = 'waiting for action'
            des_headers, des_values = None, None
        else:
            job = user['Jobs'][0]
            mode = job['mode']
            header = f'currently working: {mode_names[mode]}'
            des_headers, des_values = job_description(job)
        return [opt_list(opts), opt_list(user['Agents']), des_headers, des_values, header] \
            + [False] * len(mode_list) + [user['status'] != 'admin']
    return [NUP, [], None, None, 'waiting for action'] + [True] * (len(mode_list) + 1)


@app.callback(
    Output('user_profile', 'data'), Output('logs', 'data'),
    Input('quit', 'n_clicks')
)
def login_quit(n):
    if n:
        return None, []
    raise PreventUpdate


# Manage users
@app.callback(
    Output('users_name', 'options'), Output('alert', 'children'),
    Input('users', 'hidden'),
    State('user_profile', 'data')
)
def username_options(hidden, user):
    if hidden:
        raise PreventUpdate
    body = {
        'kind': 'name'
    }
    resp, content = api_request('POST', 'all_items', body)
    if resp == Resp.GOOD:
        content.remove(user['name'])
        return opt_list(content), NUP
    return [], general_alert(content)


@app.callback(
    Output('users_change', 'options'), Output('users_change', 'value'), Output('alert', 'children'),
    Input('users_name', 'value')
)
def user_status(name):
    if name:
        body = {
            'job': 'status_list',
            'name': name,
        }
        resp, content = api_request('POST', 'admin', body)
        if resp == Resp.GOOD:
            return opt_list(content['list']), content['status'], NUP
        return [], None, general_alert(content)
    return [], None, NUP


@app.callback(
    Output('alert', 'children'),
    Input('users_status', 'n_clicks'),
    State('users_name', 'value'), State('users_change', 'value')
)
def manage_users(n, name, status):
    if n:
        if status:
            body = {
                'job': 'status',
                'name': name,
                'status': status,
            }
            resp, content = api_request('POST', 'admin', body)
            if resp == Resp.GOOD:
                return general_alert(f'{name} status set as {status}', good=True)
            return general_alert(content)
        return general_alert('No option chosen for selected action')
    raise PreventUpdate


@app.callback(
    Output('users_name', 'options'), Output('alert', 'children'),
    Input('confirm_user_delete', 'submit_n_clicks'),
    State('users_name', 'value'), State('users_name', 'options')
)
def manage_users(n, name, options):
    if n:
        body = {
            'name': name,
            'pwd': 'x',
            'action': 'delete'
        }
        resp, content = api_request('POST', 'user', body)
        if resp == Resp.GOOD:
            options = [v for v in options if v['label'] != name]
            return options, general_alert(f'User {name} was successfully deleted', good=True),
        else:
            return NUP, general_alert(content)
    raise PreventUpdate


# Manage files
@app.callback(
    Output('files_name', 'options'), Output('alert', 'children'), Output('files_download', 'disabled'),
    Input('files_kind', 'value'),
    State('user_profile', 'data')
)
def files_options(kind, user):
    if kind and user:
        disable = kind == 'Jobs'
        if user['status'] == 'admin':
            body = {
                'kind': kind
            }
            resp, content = api_request('POST', 'all_items', body)
            if resp == Resp.GOOD:
                return opt_list(content), NUP, disable
            return NUP, general_alert(content), disable
        return opt_list(user[kind]), NUP, disable
    return [], NUP, NUP


@app.callback(
    Output('download', 'data'), Output('alert', 'children'), Output('api_update', 'n_intervals'),
    Input('files_download', 'n_clicks'), Input('files_delete', 'n_clicks'),
    State('files_kind', 'value'), State('files_name', 'value'),
    State('api_update', 'n_intervals')
)
def manage_files(n1, n2, kind, idx, interval):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[1]
    if kind is None or idx is None:
        return NUP, general_alert(f'Choose a file to {action}'), NUP
    body = {
        'kind': kind,
        'idx': idx,
        'action': action
    }
    resp, content = api_request('POST', 'file', body)
    if resp == Resp.GOOD:
        if action == 'delete':
            return NUP, general_alert(f'{idx} was successfully deleted from {kind}', good=True), interval + 1
        status, to_send = download_from_url(content)
        if status == Resp.GOOD:
            return to_send, NUP, NUP
        return NUP, general_alert(status), NUP
    return NUP, general_alert(content), NUP


# Guide
@app.callback(
    Output('guide', 'is_open'),
    Input('guide_open', 'n_clicks'), Input('guide_close', 'n_clicks')
)
def open_modal(*args):
    ctx = callback_context.triggered[0]
    if ctx['value'] is None:
        raise PreventUpdate
    trigger_id = ctx['prop_id'].split('.')[0][-1]
    return trigger_id == 'n'


@app.callback(
    Output('guide_body', 'children'),
    Input('guide_ui', 'n_clicks'), Input('guide_pd', 'n_clicks'), Input('guide_ps', 'n_clicks')
)
def guide_body(*args):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    show = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[1]
    match show:
        case 'ui':
            return dcc.Markdown(guide_interface, dedent=False, link_target='_blanc', className='app-guide_content')
        case 'ps':
            return dcc.Markdown(guide_structure, dedent=False, link_target='_blanc', className='app-guide_content')
        case 'pd':
            return [
                dcc.Markdown(guide_history[1], link_target='_blanc', className='app-guide_content'),
                html.Img(src=app.get_asset_url('score_chart_2_tile.png')),
                dcc.Markdown(guide_history[2], link_target='_blanc', className='app-guide_content'),
                html.Img(src=app.get_asset_url('score_chart_3_tile.png')),
                dcc.Markdown(guide_history[3], link_target='_blanc', className='app-guide_content'),
                html.Img(src=app.get_asset_url('score_chart_5_tile.png')),
                dcc.Markdown(guide_history[4], link_target='_blanc', className='app-guide_content')
            ]


# Game Pane and Play yourself
@app.callback(
    Output('current_game_mode', 'data'), Output('gauge_group', 'hidden'), Output('play-yourself-group', 'hidden'),
    Output('what_game', 'children'),
    Input('play_open', 'n_clicks'), Input('watch_open', 'n_clicks'), Input('replay_open', 'n_clicks')
)
def play_yourself_start(*args):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    mode = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[0]
    match mode:
        case 'play':
            return mode, True, False, mode_names[mode]
        case _:
            return mode, False, True, mode_names[mode]


@app.callback(
    Output('game_board', 'children'),
    Input('current_game', 'data')
)
def draw_board(game):
    return display_game(game)


@app.callback(
    Output('instruction', 'is_open'), Output('show_instruction', 'data'),
    Output('game_option', 'hidden'), Output('game_option_value', 'options'),
    Output('current_game', 'data'), Output('alert', 'children'),
    Input('current_game_mode', 'data'),
    State('show_instruction', 'data')
)
def play_yourself_start(mode, show_instruction):
    match mode:
        case 'play':
            game = GAME.new_game()
            return show_instruction, 0, True, NUP, game, NUP
        case x if x in ('watch', 'replay'):
            body = {
                'kind': 'Agents' if mode == 'watch' else 'Games'
            }
            resp, content = api_request('POST', 'all_items', body)
            if resp == Resp.GOOD:
                return False, NUP, False, content, EMPTY_GAME, NUP
            else:
                return False, NUP, True, NUP, EMPTY_GAME, general_alert(content)
        case _:
            return False, NUP, True, NUP, EMPTY_GAME, NUP


@app.callback(
    Output('current_game', 'data'),
    [Input(f'move_{i}', 'n_clicks') for i in range(4)] + [Input('keyboard', 'n_events')],
    State('keyboard', 'event'), State('current_game', 'data'), State('current_game_mode', 'data')
)
def button_and_keyboard_play(*args):
    if args[-1] != 'play':
        raise PreventUpdate
    game = args[-2]
    ctx = callback_context.triggered[0]
    if ctx['prop_id'] == 'keyboard.n_events':
        key = args[-3]['key']
        if not key.startswith('Arrow'):
            raise PreventUpdate
        move = keyboard_dict[key[5:]]
    else:
        move = int(ctx['prop_id'].split('.')[0][-1])
    new_game, change = GAME.make_move(game, move)
    if not change:
        raise PreventUpdate
    GAME.new_tile(new_game)
    return new_game


@app.callback(
    Output('current_game', 'data'),
    Input('restart_play', 'n_clicks')
)
def restart_play(n):
    if n:
        return GAME.new_game()
    raise PreventUpdate


# Replay Game and Watch Agent
@app.callback(
    Output('move_delay', 'disabled'),
    Input('go_game', 'n_clicks'),
    State('current_game_mode', 'data'), State('game_option_value', 'value')
)
def restart_play(n, mode, name):
    if n and name:
        return True
    raise PreventUpdate


# Agent pane
@app.callback(
    Output('current_agent_mode', 'data'), Output('agent_header', 'children'),
    Output('agent', 'hidden'), Output('train_params', 'hidden'), Output('test_params', 'hidden'),
    Input('train_open', 'n_clicks'), Input('test_open', 'n_clicks')
)
def get_agent_params(*args):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    mode = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[0]
    match mode:
        case 'train':
            return mode, 'training parameters', False, False, True
        case 'test':
            return mode, 'testing parameters', False, True, False


@app.callback(
    [Output('existing_visible', 'hidden'), Output('new_visible', 'hidden'), Output('train_p_agent_ex', 'options')]
    + [Output(f'train_p_{v}', 'value') for v in AGENT_PARAMS['train']]
    + [Output(f'train_p_{v}', 'disabled') for v in AGENT_TRAIN_LIST],
    Input('existing_new', 'value'),
    State('user_profile', 'data')
)
def toggle_training(mode, user):
    if not user:
        raise PreventUpdate
    if mode == 'Existing Agent':
        return [False, True, opt_list(user['Agents'])] \
            + [None for _ in AGENT_PARAMS['train']] \
            + [(False if v in ('min_alpha', 'episodes') else True) for v in AGENT_TRAIN_LIST]
    return [True, False, NUP] + [None, None]\
        + [AGENT_TRAIN_DEF[v] for v in AGENT_TRAIN_LIST] \
        + [False for _ in AGENT_TRAIN_LIST]


@app.callback(
    [Output(f'train_p_{v}', 'value') for v in AGENT_TRAIN_LIST],
    Input('train_p_agent_ex', 'value'),
    State('user_profile', 'data')
)
def toggle_training(agent, user):
    if agent:
        agent_params = user['Agents'][agent]
        return [agent_params[v] for v in AGENT_TRAIN_LIST[:-1]] + [AGENT_TRAIN_DEF['episodes']]
    raise PreventUpdate


@app.callback(
    Output('agent', 'hidden'), Output('api_update', 'n_intervals'), Output('alert', 'children'),
    Input('agent_btn', 'n_clicks'),
    [State('current_agent_mode', 'data'), State('user_profile', 'data'),
     State('existing_new', 'value'), State('api_update', 'n_intervals') ]
    + [State(f'train_p_{v}', 'value') for v in AGENT_PARAMS['train']]
    + [State(f'test_p_{v}', 'value') for v in AGENT_PARAMS['test']]
)
def train_test_agent(*args):
    if not args[0]:
        raise PreventUpdate
    states = {v['id']: v['value'] for v in callback_context.states_list}
    user = states['user_profile']
    running = len(user['Jobs'])
    status = user['status']
    if running >= MAX_JOBS[status]:
        return NUP, NUP, general_alert(f"You've already scheduled {running} jobs, at limit for '{status}'")
    mode = states['current_agent_mode']
    is_new = states['existing_new'] == 'New Agent'
    if mode == 'train':
        agent = states['train_p_agent_new'] if is_new else states['train_p_agent_ex']
        params = {core_id(v): states[v] for v in states if core_id(v) in AGENT_TRAIN_LIST}
    else:
        agent = states['test_p_agent']
        params = {core_id(v): states[v] for v in states if core_id(v) in AGENT_TEST_LIST}
    if agent is None or None in params.values():
        return NUP, NUP, general_alert('Some parameters are missing or invalid')
    if is_bad_name(agent):
        return NUP, NUP, general_alert('Agent name should only contain literals, numbers and "_" symbol')
    name = user['name']
    idx = f'{name}:{mode}:{agent}:{time_suffix()}'
    body = {
        'idx': idx,
        'status': 1,
        'launch': '',
        'name': name,
        'mode': mode,
        'new': is_new,
        'agent': {'idx': agent, **params}
    }
    resp, content = api_request('POST', 'slow', body)
    if resp == Resp.GOOD:
        return True, states['api_update'] + 1, NUP
    else:
        return NUP, NUP, general_alert(content)


# @app.callback(
#     Output('instruction', 'is_open'), Output('show_instruction', 'data'),
#     Output('game_option', 'hidden'), Output('game_option_value', 'options'),
#     Output('current_game', 'data'), Output('alert', 'children'),
#     Input('current_game_mode', 'data'),
#     State('show_instruction', 'data')
# )
# def play_yourself_start(mode, show_instruction):
#     match mode:
#         case 'play':
#             game = GAME.new_game()
#             return show_instruction, 0, True, NUP, game, NUP
#         case x if x in ('watch', 'replay'):
#             body = {
#                 'kind': 'Agents' if mode == 'watch' else 'Games'
#             }
#             resp, content = api_request('POST', 'all_items', body)
#             if resp == Resp.GOOD:
#                 return False, NUP, False, content, EMPTY_GAME, NUP
#             else:
#                 return False, NUP, True, NUP, EMPTY_GAME, general_alert(content)
#         case _:
#             return False, NUP, True, NUP, EMPTY_GAME, NUP


# refresh status, to keep parallel processes from closing down while the app is open in the browser,
# script "vacuum_cleaner" is killing them afterwards
# @app.callback(
#     Output('refresh_status', 'disabled'),
#     Input('refresh_status', 'n_intervals'),
#     State('session_tags', 'data')
# )
# def refresh_status(n, tags):
#     if n:
#         RUNNING[tags['parent']] = 1
#         # memo_text = load_s3('memory_usage.txt')
#         # save_s3(memo_text + memory_usage_line(), 'memory_usage.txt')
#         if tags:
#             status = load_s3('status.json')
#             next_check = next_time()
#             for key in status:
#                 value = tags[key]
#                 if value in status[key]:
#                     status[key][value]['finish'] = next_check
#             save_s3(status, 'status.json')
#     raise PreventUpdate
#
#
# # Project description callbacks
# @app.callback(
#     Output('guide_page', 'is_open'),
#     Input('description_button', 'n_clicks'),
# )
# def toggle_guide_page(n):
#     return bool(n)
#
#
# @app.callback(
#     Output('guide_page_body', 'children'),
#     Input('guide_project_button', 'n_clicks'),
# )
# def show_project_description(n):
#     if n:
#         return [
#             dcc.Markdown(project_description[1], link_target='_blanc', className='md_content'),
#             html.Img(src=app.get_asset_url('score_chart_2_tile.png')),
#             dcc.Markdown(project_description[2], link_target='_blanc', className='md_content'),
#             html.Img(src=app.get_asset_url('score_chart_3_tile.png')),
#             dcc.Markdown(project_description[3], link_target='_blanc', className='md_content'),
#             html.Img(src=app.get_asset_url('score_chart_5_tile.png')),
#             dcc.Markdown(project_description[4], link_target='_blanc', className='md_content')
#         ]
#     else:
#         raise PreventUpdate
#
#
# # Project description callbacks
# @app.callback(
#     Output('guide_page_body', 'children'),
#     Input('guide_ui_button', 'n_clicks'),
# )
# def show_ui_description(n):
#     return dcc.Markdown(interface_description, dedent=False, link_target='_blanc', className='md_content')
#
#
# # admin page callbacks
# @app.callback(
#     Output('admin_page', 'is_open'),
#     Input('open_admin', 'n_clicks'), Input('close_admin', 'n_clicks'),
#     State('admin_page', 'is_open'),
# )
# def toggle_admin_page(n1, n2, is_open):
#     if n1 or n2:
#         return not is_open
#     return is_open
#
#
# @app.callback(
#     Output('choose_file', 'options'), Output('choose_file', 'value'), Output('admin_go', 'children'),
#     [Input(v, 'n_clicks') for v in act_list]
# )
# def act_process(*args):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise PreventUpdate
#     idx = ctx.triggered[0]['prop_id'].split('.')[0]
#     if idx == 'upload':
#         files = ['config file', 'game', 'agent']
#     elif idx == 'download':
#         files = list_names_s3()
#     else:
#         files = [v for v in list_names_s3() if v != 'status.json']
#     value = 'config file' if idx == 'upload' else None
#     return [{'label': v, 'value': v} for v in files], value, act_list[idx]
#
#
# @app.callback(
#     Output('admin_notification', 'children'), Output('download_file', 'data'),
#     Input('admin_go', 'n_clicks'),
#     State('admin_go', 'children'), State('choose_file', 'value')
# )
# def admin_act(n, act, name):
#     if n:
#         if act == 'Delete':
#             if name:
#                 delete_s3(name)
#                 return my_alert(f'{name} deleted'), NUP
#             else:
#                 return my_alert(f'Choose file to delete!', info=True), NUP
#         elif act == 'Download':
#             if name:
#                 return NUP, dash_send(name)
#             else:
#                 return my_alert(f'Choose file for download!', info=True), NUP
#         raise PreventUpdate
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('data_uploader', 'style'),
#     Input('admin_go', 'children')
# )
# def show_upload(act):
#     return {'display': 'block' if act == 'Upload' else 'none'}
#
#
# @app.callback(
#     Output('admin_notification', 'children'), Output('uploading', 'className'),
#     Input('data_uploader', 'filename'), State('data_uploader', 'contents'),
#     State('choose_file', 'value')
# )
# def upload_process(name, content, kind):
#     if name:
#         file_data = content.encode("utf8").split(b";base64,")[1]
#         with open(name, "wb") as f:
#             f.write(base64.decodebytes(file_data))
#         prefix = 'c/' if kind == 'config file' else ('g/' if kind == 'game' else 'a/')
#         s3_bucket.upload_file(name, prefix + name)
#         os.remove(name)
#         return my_alert(f'Uploaded {name} as new {kind}'), NUP
#     else:
#         raise PreventUpdate
#
#
# # Control Panel callbacks
# @app.callback(
#     Output('mode_text', 'children'), Output('input_group_agent', 'style'), Output('input_group_game', 'style'),
#     Output('input_group_train', 'style'), Output('num_eps', 'style'),
#     [Input(v, 'n_clicks') for v in mode_list]
# )
# def mode_process(*args):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise PreventUpdate
#     idx = ctx.triggered[0]['prop_id'].split('.')[0]
#     to_see_games = 'block' if idx == 'replay_button' else 'none'
#     to_see_agents = 'block' if idx in ('watch_agent_button', 'agent_stat_button') else 'none'
#     to_train_agent = 'block' if idx == 'train_agent_button' else 'none'
#     to_test_agent = 'block' if idx == 'agent_stat_button' else 'none'
#     return mode_list[idx][1], {'display': to_see_agents}, {'display': to_see_games}, \
#         {'display': to_train_agent}, {'display': to_test_agent}
#
#
# # Game Replay callbacks
# @app.callback(
#     Output('choose_for_replay', 'options'),
#     Input('input_group_game', 'style')
# )
# def find_games(style):
#     if style['display'] == 'none':
#         raise PreventUpdate
#     games = [v for v in list_names_s3() if v[:2] == 'g/']
#     return [{'label': v[2:-4], 'value': v} for v in games]
#
#
# @app.callback(
#     Output('replay_game_button', 'disabled'),
#     Input('choose_for_replay', 'value')
# )
# def enable_replay_game_button(name):
#     return not bool(name)
#
#
# @app.callback(
#     Output('update_interval', 'disabled'), Output('choose_for_replay', 'value'), Output('idx', 'data'),
#     Input('replay_game_button', 'n_clicks'),
#     State('choose_for_replay', 'value'), State('idx', 'data')
# )
# def replay_game(n, game_file, idx):
#     if n and idx:
#         game = load_s3(game_file)
#         idx['n'] += 1
#         GAME_PANE[idx['parent']] = {
#             'id': idx['n'],
#             'type': 'game',
#             'games': game.replay(verbose=False),
#             'step': 0
#         }
#         return False, None, idx
#     else:
#         raise PreventUpdate
#
#
# # Board Refresh for "Game Replay" and "Agent Play" functions
# @app.callback(
#     Output('game_card', 'children'), Output('update_interval', 'disabled'),
#     Input('update_interval', 'n_intervals'),
#     State('idx', 'data')
# )
# def refresh_board(n, idx):
#     if n and idx:
#         point = GAME_PANE.get(idx['parent'], False)
#         if not point:
#             raise PreventUpdate
#
#         # Game Replay
#         if point['type'] == 'game':
#             step = point['step']
#             if step == -1:
#                 return NUP, True
#             row, score, next_move = point['games'][step]
#         # Agent Play
#         elif point['type'] == 'agent':
#             step, game = point['step'], point['game']
#             if point['step'] >= game.odometer and not game.game_over(game.row):
#                 return NUP, NUP
#             if step == -1:
#                 return NUP, True
#             row, score, next_move = game.history[step]
#         # Play Yourself
#         else:
#             raise PreventUpdate
#
#         to_show = display_table(row, score, step, next_move)
#         point['step'] = -1 if next_move == -1 else point['step'] + 1
#         return to_show, NUP
#     else:
#         raise PreventUpdate
#
#
# # Agent Play callbacks
# @app.callback(
#     Output('choose_stored_agent', 'options'),
#     Input('input_group_agent', 'style')
# )
# def find_agents(style):
#     if style['display'] == 'none':
#         raise PreventUpdate
#     agents = [v for v in list_names_s3() if v[:2] == 'a/']
#     return [{'label': v[2:-4], 'value': v} for v in agents]
#
#
# @app.callback(
#     Output('replay_agent_button', 'disabled'),
#     Input('choose_stored_agent', 'value')
# )
# def enable_agent_play_button(name):
#     if name:
#         return False
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('update_interval', 'disabled'), Output('idx', 'data'), Output('agent_play_loading', 'className'),
#     Input('replay_agent_button', 'n_clicks'),
#     State('mode_text', 'children'), State('choose_stored_agent', 'value'), State('choose_depth', 'value'),
#     State('choose_width', 'value'), State('choose_since_empty', 'value'), State('idx', 'data'),
# )
# def start_agent_play(n, mode, agent_file, depth, width, empty, idx):
#     if n and mode == 'Watch Agent':
#         agent = QAgent.load_agent(agent_file)
#         estimator = agent.evaluate
#         game = Game()
#         idx['n'] += 1
#         GAME_PANE[idx['parent']] = {
#             'id': idx['n'],
#             'type': 'agent',
#             'game': game,
#             'step': 0,
#         }
#         game.thread_trial(estimator, depth=depth, width=width, since_empty=empty, stopper=idx)
#         return False, idx, NUP
#     else:
#         raise PreventUpdate
#
#
# # Agent Test callbacks
# @app.callback(
#     Output('stop_agent', 'style'), Output('idx', 'data'), Output('test_loading', 'className'),
#     Output('train_agent_button', 'disabled'), Output('agent_stat_button', 'disabled'),
#     Input('replay_agent_button', 'n_clicks'),
#     State('mode_text', 'children'),  State('choose_stored_agent', 'value'), State('choose_depth', 'value'),
#     State('choose_width', 'value'), State('choose_since_empty', 'value'), State('choose_num_eps', 'value'),
#     State('log_file', 'data'), State('idx', 'data')
# )
# def start_agent_test(n, mode, agent_file, depth, width, empty, num_eps, log_file, idx):
#     if n and mode == 'Test Agent':
#         idx['a'] += 1
#         AGENT_PANE[idx['parent']] = {
#             'id': idx['a'],
#             'type': 'test'
#         }
#         params = {'depth': depth, 'width': width, 'since_empty': empty, 'num': num_eps, 'console': 'web',
#                   'log_file': log_file, 'game_file': 'g/best_of_last_trial.pkl', 'agent_file': agent_file,
#                   'stopper': idx}
#         add_to_memo(f'{str(datetime.now())[11:]} start TEST on click {n}\n')
#         Thread(target=QAgent.trial, kwargs=params, daemon=True).start()
#         return {'display': 'block'}, idx, NUP, True, True
#     else:
#         raise PreventUpdate
#
#
# # Agent Train callbacks
# @app.callback(
#     Output('choose_train_agent', 'options'), Output('choose_train_agent', 'value'),
#     Output('choose_config', 'options'), Output('choose_config', 'value'),
#     Input('input_group_train', 'style')
# )
# def find_agents(style):
#     if style['display'] == 'none':
#         raise PreventUpdate
#     agents = [v for v in list_names_s3() if v[:2] == 'a/']
#     configs = [v for v in list_names_s3() if v[:2] == 'c/']
#     agent_options = [{'label': v[2:-4], 'value': v} for v in agents] + [{'label': 'New agent', 'value': 'New agent'}]
#     conf_options = [{'label': v[2:-5], 'value': v} for v in configs] + [{'label': 'New config', 'value': 'New config'}]
#     return agent_options, None, conf_options, None
#
#
# @app.callback(
#     Output('choose_config', 'value'), Output('choose_config', 'disabled'),
#     Input('choose_train_agent', 'value')
# )
# def open_train_params(agent):
#     if agent == 'New agent':
#         return None, False
#     elif agent:
#         return NUP, True
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('go_to_params', 'disabled'),
#     Input('choose_train_agent', 'value'),
#     Input('choose_config', 'value')
# )
# def open_train_params(agent, config):
#     return not agent or (agent == 'New agent' and not config)
#
#
# @app.callback(
#     Output('params_page', 'is_open'), Output('start_training', 'disabled'),
#     Input('go_to_params', 'n_clicks')
# )
# def open_params_page(n):
#     if n:
#         return True, True
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('params_page', 'is_open'),
#     Input('close_params', 'n_clicks'),
# )
# def close_params_page(n):
#     if n:
#         return False
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     [Output(f'par_{e}', 'disabled') for e in params_list] + [Output(f'par_{e}', 'value') for e in params_list] +
#     [Output('start_training', 'disabled'), Output('fill_loading', 'className')],
#     Input('params_page', 'is_open'),
#     State('choose_train_agent', 'value'), State('choose_config', 'value'),
# )
# def fill_params(is_open, agent_name, config_name):
#     if is_open:
#         if agent_name != 'New agent':
#             agent = load_s3(agent_name)
#             dis = [params_dict[e]['disable'] for e in params_list]
#             ui_params = [getattr(agent, e) for e in params_list[:-1]] + [params_dict['Training episodes']['value']]
#         elif config_name != 'New config':
#             config = load_s3(config_name)
#             dis = [False for _ in params_list]
#             ui_params = [config.get(e, params_dict[e]['value']) for e in params_list]
#         else:
#             dis = [False for _ in params_list]
#             ui_params = [params_dict[e]['value'] for e in params_list]
#         return dis + ui_params + [False, NUP]
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('params_notification', 'children'), Output('choose_train_agent', 'options'),
#     Output('choose_train_agent', 'value'), Output('start_training', 'disabled'), Output('loading', 'className'),
#     Output('mode_text', 'children'), Output('input_group_train', 'style'), Output('stop_agent', 'style'),
#     Output('train_agent_button', 'disabled'), Output('agent_stat_button', 'disabled'),
#     Output('session_tags', 'data'), Output('idx', 'data'),
#     Input('start_training', 'n_clicks'),
#     [State(f'par_{e}', 'value') for e in params_list] +
#     [State('choose_train_agent', 'value'), State('log_file', 'data'),
#      State('session_tags', 'data'), State('idx', 'data')]
# )
# def start_training(*args):
#     if args[0]:
#         message = NUP
#         new_name, new_agent_file, log_file, tags, idx = args[1], args[-4], args[-3], args[-2], args[-1]
#         ui_params = {e: args[i + 2] for i, e in enumerate(params_list[1:])}
#         ui_params['n'] = int(ui_params['n'])
#         bad_inputs = [e for e in ui_params if ui_params[e] is None]
#         if bad_inputs:
#             return [my_alert(f'Parameters {bad_inputs} unacceptable', info=True)] + [NUP] * 11
#         name = ''.join(x for x in new_name if (x.isalnum() or x in ('_', '.')))
#         if name == 'test_agent':
#             name = f'agent_{time_suffix(6)}'
#         num_eps = ui_params.pop('Training episodes')
#         if new_agent_file == 'New agent':
#             if f'a/{name}.pkl' in list_names_s3():
#                 return [my_alert(f'Agent with {name} already exists!', info=True)] + [NUP] * 11
#             new_config_file = f'c/config_{name}.json'
#             save_s3(ui_params, new_config_file)
#             message = my_alert(f'new config file {new_config_file[2:]} saved')
#             current = QAgent(name=name, config_file=new_config_file, with_weights=False)
#             add_weights = 'add'
#         else:
#             current = load_s3(new_agent_file)
#             add_weights = f'weights/{current.name}.pkl'
#             if current.name != name:
#                 if f'a/{name}.pkl' in list_names_s3():
#                     return [my_alert(f'Agent with {name} already exists!', info=True)] + [NUP] * 11
#                 current.name = name
#                 current.file = current.name + '.pkl'
#                 current.game_file = 'best_of_' + current.file
#             else:
#                 if name in load_s3('status.json')['agent']:
#                     return [my_alert(f'Agent {name} is being trained by another user', info=True)] + [NUP] * 11
#             for e in ui_params:
#                 setattr(current, e, ui_params[e])
#         idx['a'] += 1
#         AGENT_PANE[idx['parent']] = {
#             'id': idx['a'],
#             'type': 'train'
#         }
#         current.log_file = log_file
#         current.print = Logger(log_file=log_file).add
#         add_status('agent', name, tags['parent'])
#         tags['agent'] = name
#         add_to_memo(f'{str(datetime.now())[11:]} start TRAIN on click {args[0]}\n')
#         Thread(target=current.train_run, kwargs={'num_eps': num_eps, 'add_weights': add_weights, 'stopper': idx},
#                daemon=True).start()
#         if name != new_name:
#             agents = [v for v in list_names_s3() if v[:2] == 'a/']
#             opts = [{'label': v[2:-4], 'value': v} for v in agents] + [{'label': 'New agent', 'value': 'New agent'}]
#         else:
#             opts = NUP
#         return message, opts, f'a/{current.file}', True, NUP, 'Choose:', {'display': 'none'}, {'display': 'block'}, \
#             True, True, tags, idx
#     else:
#         raise PreventUpdate
#
#
# # Game Board callbacks
# @app.callback(
#     Output('gauge', 'value'), Output('update_interval', 'interval'),
#     Input('gauge-slider', 'value')
# )
# def update_output(value):
#     return value, value * 200 + LOWEST_SPEED
#
#
# @app.callback(
#     Output('update_interval', 'disabled'),
#     Input('pause_game', 'n_clicks')
# )
# def pause_game(n):
#     return bool(n)
#
#
# @app.callback(
#     Output('update_interval', 'disabled'),
#     Input('resume_game', 'n_clicks')
# )
# def resume_game(n):
#     return not bool(n)
#
#
# # Chart callbacks
# @app.callback(
#     Output('chart_button', 'style'), Output('chart_button', 'children'), Output('agent_for_chart', 'data'),
#     Input('choose_train_agent', 'value'), Input('choose_stored_agent', 'value')
# )
# def enable_chart_button(*args):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise PreventUpdate
#     agent = ctx.triggered[0]['value']
#     if agent is None or agent == 'New agent':
#         raise PreventUpdate
#     return {'display': 'block'}, f'{agent[2: -4]} train history chart', agent
#
#
# @app.callback(
#     Output('chart_page', 'is_open'),
#     Input('chart_button', 'n_clicks'), Input('close_chart', 'n_clicks'),
#     State('chart_page', 'is_open'),
# )
# def toggle_chart_page(n1, n2, is_open):
#     if n1 or n2:
#         return not is_open
#     return is_open
#
#
# @app.callback(
#     Output('chart_header', 'children'), Output('chart', 'children'), Output('chart_loading', 'className'),
#     Input('chart_page', 'is_open'),
#     State('agent_for_chart', 'data')
# )
# def make_chart(is_open, agent_file):
#     if is_open:
#         agent = load_s3(agent_file)
#         if agent is None:
#             return '', f'No Agent with this name in storage', NUP
#         history = agent.train_history
#         header = f'Training history of {agent.name}'
#         if not history:
#             return header, 'No history yet', NUP
#         x = np.array([v * 100 for v in range(1, len(history) + 1)])
#         fig = px.line(x=x, y=history, labels={'x': 'number of episodes', 'y': 'Average score of last 100 games'})
#         return header, dcc.Graph(figure=fig, style={'width': '100%', 'height': '100%'}), NUP
#     else:
#         raise PreventUpdate
#
#
# # Play Yourself callbacks
# @app.callback(
#     Output('play_instructions', 'is_open'), Output('gauge_group', 'style'), Output('play-yourself-group', 'style'),
#     Output('update_interval', 'disabled'), Output('game_card', 'children'), Output('idx', 'data'),
#     Input('mode_text', 'children'),
#     State('idx', 'data')
# )
# def play_yourself_start(mode, idx):
#     if mode:
#         if mode == 'Play':
#             game = Game()
#             idx['n'] += 1
#             GAME_PANE[idx['parent']] = {
#                 'id': idx['n'],
#                 'type': 'play',
#                 'game': game
#             }
#             to_show = display_table(game.row, game.score, game.odometer, 0, self_play=True)
#             return True, {'display': 'none'}, {'display': 'block'}, True, to_show, idx
#         else:
#             return False, {'display': 'block'}, {'display': 'none'}, NUP, NUP, NUP
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('game_card', 'children'),
#     [Input(f'move_{i}', 'n_clicks') for i in range(4)] + [Input('keyboard', 'event')],
#     State('mode_text', 'children'), State('idx', 'data')
# )
# def button_and_keyboard_play(*args):
#     ctx = dash.callback_context.triggered[0]
#     if args[-2] == 'Play' and ctx['prop_id'] != '.':
#         if ctx['prop_id'] == 'keyboard.event':
#             key = ctx['value']['key']
#             if not key.startswith('Arrow'):
#                 raise PreventUpdate
#             move = keyboard_dict[key[5:]]
#         else:
#             move = int(ctx['prop_id'].split('.')[0][-1])
#         game = GAME_PANE[args[-1]['parent']]['game']
#         new_row, new_score, change = game.pre_move(game.row, game.score, move)
#         if not change:
#             raise PreventUpdate
#         game.odometer += 1
#         game.row, game.score = new_row, new_score
#         game.new_tile()
#         next_move = -1 if game.game_over(game.row) else 0
#         return display_table(game.row, game.score, game.odometer, next_move, self_play=True)
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('game_card', 'children'),
#     Input('restart_play', 'n_clicks'),
#     State('idx', 'data')
# )
# def restart_play(n, idx):
#     if n:
#         game = Game()
#         GAME_PANE[idx['parent']]['game'] = game
#         return display_table(game.row, game.score, game.odometer, 0, self_play=True)
#     else:
#         raise PreventUpdate
#
#
# # Log window callbacks
# @app.callback(
#     Output('log_file', 'data'), Output('session_tags', 'data'), Output('initiate_logs', 'disabled'),
#     Output('description_button', 'n_clicks'), Output('mode_menu', 'disabled'), Output('idx', 'data'),
#     Input('initiate_logs', 'n_intervals')
# )
# def assign_log_file(n):
#     if n:
#         # save_s3(f'Memory usage:\n{memory_usage_line()}', 'memory_usage.txt')
#         log_file = f'l/logs_{time_suffix(6)}.txt'
#         parent = f'{os.getpid()}_{time_suffix(6)}'
#         GAME_PANE[parent] = {}
#         AGENT_PANE[parent] = {}
#         RUNNING[parent] = 1
#         tags = {'parent': parent, 'logs': log_file, 'agent': 'none'}
#         add_status('logs', log_file, tags['parent'])
#         return log_file, tags, True, 1, False, {'parent': parent, 'n': 0, 'a': 0}
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('vc', 'disabled'),
#     Input('vc', 'n_intervals')
# )
# def vacuum_cleaner(n):
#     if n:
#         status: dict = load_s3('status.json')
#         now = datetime.utcnow()
#         for key in status:
#             to_delete = []
#             for value in status[key]:
#                 finish = parser.parse(status[key][value]['finish'])
#                 if now > finish:
#                     if key == 'logs':
#                         delete_s3(value)
#                     to_delete.append(value)
#             for v in to_delete:
#                 if v in status[key]:
#                     del status[key][v]
#
#         save_s3(status, 'status.json')
#     raise PreventUpdate
#
#
# @app.callback(
#     Output('log_footer', 'children'),
#     Input('running_now', 'data')
# )
# def populate_log_footer(data):
#     if data:
#         return Logger.msg[data]
#     else:
#         return Logger.msg['welcome']
#
#
# @app.callback(
#     Output('logs_display', 'children'),
#     Input('logs_interval', 'n_intervals'),
#     State('log_file', 'data')
# )
# def update_logs(n, log_file):
#     if n:
#         return load_s3(log_file)
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('logs_display', 'children'),
#     Input('clear_logs', 'n_clicks'),
#     State('log_file', 'data')
# )
# def clear_logs(n, log_file):
#     if n:
#         save_s3('', log_file)
#         return None
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('download_file', 'data'),
#     Input('download_logs', 'n_clicks'),
#     State('logs_display', 'children'),
# )
# def download_logs(n, current_logs):
#     if n and current_logs:
#         temp = f'temp{time_suffix()}.txt'
#         with open(temp, 'w') as f:
#             f.write(current_logs)
#         to_send = dcc.send_file(temp)
#         os.remove(temp)
#         return to_send
#     else:
#         raise PreventUpdate
#
#
# @app.callback(
#     Output('stop_agent', 'style'),
#     Input('current_process', 'data'),
# )
# def enable_stop_agent_button(current_process):
#     return {'display': 'block' if current_process else 'none'}
#
#
# @app.callback(
#     Output('stop_agent', 'style'), Output('session_tags', 'data'),
#     Output('train_agent_button', 'disabled'), Output('agent_stat_button', 'disabled'),
#     Input('stop_agent', 'n_clicks'),
#     State('idx', 'data'), State('session_tags', 'data')
# )
# def stop_agent(n, idx, tags):
#     if n:
#         AGENT_PANE[idx['parent']]['id'] = -1
#         if AGENT_PANE[idx['parent']]['type'] == 'train':
#             status: dict = load_s3('status.json')
#             status['agent'].pop(tags['agent'], None)
#             save_s3(status, 'status.json')
#             tags['agent'] = 'none'
#         return {'display': 'none'}, tags, False, False
#     else:
#         raise PreventUpdate

for v in modals_draggable:
    app.clientside_callback(
        ClientsideFunction(namespace='drag_div', function_name='drag_div'),
        Output(v, 'className'),
        Input(v, 'id')
    )

app.clientside_callback(
    ClientsideFunction(namespace='drag_toast', function_name='drag_toast'),
    Output('instruction', 'className'),
    Input('instruction', 'is_open'), State('instruction', 'id')
)


if __name__ == '__main__':

    app.run_server(host='0.0.0.0', port=int(os.environ.get("PORT", 4000)), debug=LOCAL, use_reloader=False)
