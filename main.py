from base.dash_utils import *

dash_directory = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dash_directory, 'assets', 'user_guide.md'), 'r') as f:
    guide_interface = f.read()
with open(os.path.join(dash_directory, 'assets', 'structure.md'), 'r') as f:
    guide_structure = f.read()
guide_history = {}
for i in (1, 2, 3, 4):
    with open(os.path.join(dash_directory, 'assets', f'project_{i}.md'), 'r') as f:
        guide_history[i] = f.read()

CACHE = diskcache.Cache('./cache')
BCM = DiskcacheLongCallbackManager(CACHE)
app = DashProxy(__name__, suppress_callback_exceptions=True, background_callback_manager=BCM,
                transforms=[MultiplexerTransform()], title='RL Agent 2048', update_title=None,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])

app.layout = dbc.Container([
    dcc.Interval(id='api_update', interval=5000, n_intervals=1, disabled=True),
    dcc.Store(id='user_profile', storage_type='session', data=None),
    dcc.Store(id='logs', storage_type='session', data=[]),
    dcc.Store(id='max_logs', storage_type='session'),
    dcc.Store(id='current_game_mode', storage_type='session'),
    dcc.Store(id='current_game', data=EMPTY_GAME, storage_type='session'),
    dcc.Store(id='moves_tiles', storage_type='session', data=None),
    dcc.Store(id='current_move', storage_type='session', data=0),
    dcc.Store(id='current_agent_mode', storage_type='session'),
    dcc.Store(id='show_instruction', storage_type='session', data=1),
    EventListener(id='keyboard'),
    dcc.Interval(id='move_delay', n_intervals=0, disabled=True),
    dcc.Store(id='tmp_user', storage_type='session'),
    dcc.Interval(id='tmp_update', interval=3000, n_intervals=0, disabled=True),
    dcc.Download(id='download'),
    html.Div(id='alert'),
    dcc.ConfirmDialog(id='confirm_delete',
                      message='Are you sure? All Agents assigned to this user will be deleted'),
    dcc.ConfirmDialog(id='confirm_user_delete',
                      message='Are you sure? All Agents assigned to this user will be deleted'),
    dbc.NavbarSimple(
        children=[
            dbc.Button('Contacts', id='contacts_open', className='app-btn', color='info', disabled=True),
            dbc.Button('Manage Users', id='users_open', className='app-btn app-r1', color='primary', disabled=True),
            dbc.Button('My Objects', id='files_open', className='app-btn app-r1', color='primary', disabled=True),
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
        dbc.NavLink(mode_names[v], id=f'{v}_open', disabled=(v in mode_names_disabled),
                    className='app-nav-item' + (' app-odd-item' if i % 2 else ''))
        for i, v in enumerate(list(mode_names))
        ], id='navbar', links_left=True, className='app-table-nav'),
    html.Div([
        dbc.ModalHeader('registration', close_button=False, id='login_header', className='app-modal-header'),
        dbc.ModalBody(children=[
            dbc.Input(id='login_name', className='app-input-field login-name', type='text', placeholder='User'),
            dbc.Input(id='login_pwd', className='app-input-field login-pwd', type='password', placeholder='Password'),
            html.Div('* Need to register to unlock Agent Train/Test functions', className='app-comment')
        ], className='app-modal-body'),
        dbc.ModalFooter([
            dbc.Button('Submit', id='login_submit', className='app-btn app-btn-submit', n_clicks=0, color='success'),
            dbc.Button('New User', id='login_new', className='app-btn app-r1', n_clicks=0, color='primary'),
            dbc.Button('Quit', id='login_close', className='app-btn app-r1', n_clicks=0, color='warning')
        ], className='app-modal-footer')
    ], id='login', className='app-border', hidden=False),
    html.Div([
        dbc.ModalHeader('Manage My Objects', close_button=False, id='files_header', className='app-modal-header'),
        dbc.ModalBody(children=[
            html.Div('Agents/Games ?'),
            dcc.Dropdown(id='files_kind', options=opt_list(FIELDS), clearable=False),
            html.Div('Name:'),
            dcc.Dropdown(id='files_name'),
            html.Div(id='files_description', className='app-files-description')
        ], className='app-modal-body'),
        dbc.ModalFooter([
            dbc.Button('Delete', id='files_delete', className='app-btn app-btn-submit', color='success'),
            dbc.Button('Weights', id='files_weights', className='app-btn app-r1', color='primary', disabled=False,
                       style={'visibility': 'hidden'}),
            dbc.Button('Download', id='files_download', className='app-btn app-r1', color='primary', disabled=False),
            dbc.Button('Quit', id='files_close', className='app-btn app-r1', color='warning')
        ], className='app-modal-footer')
    ], id='files', className='app-border', hidden=True),
    html.Div([
        dbc.ModalHeader('manage users', close_button=False, id='users_header', className='app-modal-header'),
        dbc.ModalBody(children=[
            html.Div('User :'),
            dcc.Dropdown(id='users_name', clearable=False),
            html.Div('New Status'),
            dcc.Dropdown(id='users_change', clearable=False),
            html.Div(id='user_description', className='app-files-description')
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
                    dbc.Button('Interface', id='guide_ui', className='app-btn app-btn-group', color='info'),
                    dbc.Button('History', id='guide_pd', className='app-btn app-btn-group', color='primary'),
                    dbc.Button('Structure', id='guide_ps', className='app-btn app-btn-group', color='secondary'),
                ]),
                dbc.Button('Quit', id='guide_close', className='app-btn', color='warning')
            ],
            close_button=False, id='guide_header'),
        dbc.ModalBody(id='guide_body'),
    ], id='guide', size='xl', contentClassName='app-guide-body', className='app-border', scrollable=True),
    html.Div([
        dbc.ModalBody(id='chart_body', className='app-chart-body'),
        dbc.ModalFooter([
            dbc.Button('Quit', id='chart_close', className='app-btn', color='warning')
        ], className='app-modal-footer')
    ], id='chart', className='app-border', hidden=True),
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
                                + [params_line('train', p) for p in AGENT_TRAIN_LIST], className='app-train-box')
                        ], id='train_params', hidden=True),
                        html.Div([
                            html.Div([
                                params_line('test', p) for p in AGENT_PARAMS['test']], className='app-test-box'),
                            dbc.Button('Training Chart', id='chart_open', className='app-btn app-btn-chart',
                                       color='primary', disabled=True)
                        ], id='test_params', hidden=True)
                    ], className='app-modal-body'),
                    dbc.ModalFooter([
                        dbc.Button('Go!', id='agent_btn', className='app-btn app-btn-submit', color='success'),
                        dbc.Button('Quit', id='agent_close', className='app-btn', color='warning')
                    ], className='app-modal-footer')
                ], id='agent', className='app-border', hidden=True),
                html.Div('Waiting for action', id='what_agent', className='app-pane-header'),
                dbc.Row([
                    dbc.Col(html.Div(id='current_job_headers')),
                    dbc.Col(html.Div(id='current_job_values', className='app-job-values'), className='app-col-values'),
                    dbc.Col([
                        dbc.Button('Stop Job', id='stop_job', className='app-btn app-stop-job', color='info'),
                        dbc.Button('Kill Job', id='kill_job', className='app-btn app-kill-job', color='warning'),
                    ])
                ], className='app-agent-window'),
                html.Div(id='logs_window', className='app-logs-window'),
                dbc.Button('Download', id='download_logs', className='app-btn app-download-logs', color='info'),
                dbc.Button('Clear logs', id='clear_logs', className='app-btn app-clear-logs', color='primary'),
            ], className='app-pane align-items-center')
        ),
        dbc.Col(
            dbc.Card([
                html.Div([
                    dbc.ModalHeader(close_button=False, id='game_header', className='app-modal-header'),
                    dbc.ModalBody(children=[
                        html.Div([
                            dbc.RadioItems(('New game', 'From current position'), value='New game',
                                           inline=True, id='finish_game', className='app-train-radio'),
                            html.Div([
                                params_line('watch', p) for p in AGENT_PARAMS['watch']], className='app-watch-box'),
                        ], id='watch_params', hidden=True),
                        html.Div([
                            html.Br(),
                            dbc.InputGroup([
                                dbc.InputGroupText('Game', className='app-par-text'),
                                dbc.Select(id='replay_game', className='no-border')], style={'margin': '0.1rem'})
                        ], id='replay_params', hidden=True)
                    ], className='app-modal-body'),
                    dbc.ModalFooter([
                        dbc.Button('Go!', id='game_go', className='app-btn app-btn-submit', color='success'),
                        dbc.Button('Quit', id='game_close', className='app-btn', color='warning')
                    ], className='app-modal-footer')
                ], id='game', className='app-border', hidden=True),
                dcc.Loading(id='loading_progress', type='cube', color='#f0ad4e',
                            style={'position': 'absolute', 'top': '10rem', 'z-index': '300'}),
                dbc.Toast(self_play_instruction, header='Game instructions', headerClassName='inst-header',
                          id='instruction', className='app-border', dismissable=True, is_open=False),
                html.Div('Waiting for action', id='what_game', className='app-pane-header'),
                html.Div(EMPTY_BOARD, id='game_board'),
                # dbc.CardBody(EMPTY_BOARD, id='game_board'),
                html.Div([
                    daq.Gauge(id='gauge', className='gauge',
                              color={"gradient": True, "ranges": {"blue": [0, 6], "yellow": [6, 8], "red": [8, 10]}}),
                    html.Div('DELAY', className='app-speed-header'),
                    dcc.Slider(id='gauge_slider', min=0, max=10, value=3, marks={v: str(v) for v in range(11)},
                               step=0.1, className='app-speed-slider'),
                    html.Div([
                        dbc.Button('PAUSE', id='pause_game', className='app-btn app-pause-btn', color='info'),
                        dbc.Button('ONCE MORE', id='go_again', className='app-btn app-again-btn', color='success'),
                        dbc.Button('RESUME', id='resume_game', className='app-btn app-resume-btn'),
                    ], className='app-button-line')
                ], id='gauge_group', className='app-gauge-group', hidden=False),
                html.Div([
                    dbc.Button('\u2190', id='move_0', className='move-button move-left'),
                    dbc.Button('\u2191', id='move_1', className='move-button move-up'),
                    dbc.Button('\u2192', id='move_2', className='move-button move-right'),
                    dbc.Button('\u2193', id='move_3', className='move-button move-down'),
                    dbc.Button('RESTART', id='restart_play', className='app-btn app-restart-btn', color='success'),
                ], id='play-yourself-group', className='app-gauge-group', hidden=True),
            ], className='app-pane align-items-center'),
        )
    ])
], className='app-cont', fluid=True)


# general callbacks
for v in divs_open_close:
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

for v in modal_open_close:
    @app.callback(
        Output(v, 'is_open'),
        Input(f'{v}_open', 'n_clicks'), Input(f'{v}_close', 'n_clicks')
    )
    def open_modal(*args):
        ctx = callback_context.triggered[0]
        if ctx['value'] is None:
            raise PreventUpdate
        trigger_id = ctx['prop_id'].split('.')[0][-1]
        return trigger_id == 'n'

for v in divs_just_close:
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


@app.callback(
    [Output(v, 'hidden') for v in divs_only_one_open],
    [Input(v, 'hidden') for v in divs_only_one_open]
)
def only_one_open(*args):
    ctx = callback_context
    if not ctx.triggered or ctx.triggered[0]['value']:
        raise PreventUpdate
    to_open = ctx.triggered[0]['prop_id'].split('.')[0]
    return [(True if v != to_open else False) for v in divs_only_one_open]


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


@app.callback(
    Output('download', 'data'),
    Input('download_logs', 'n_clicks'),
    State('logs', 'data')
)
def update_logs(n, logs):
    if n:
        temp = f'temp{time_suffix()}.txt'
        with open(temp, 'w') as f:
            f.write('\n'.join(logs))
        to_send = dcc.send_file(temp)
        os.remove(temp)
        return to_send
    raise PreventUpdate


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
        return NUP, NUP, NUP, NUP, general_alert('User name should only contain literals, numbers and "_" symbol'), \
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
    [Output(f'{v}_open', 'disabled') for v in mode_names_disabled],
    Input('user_profile', 'data')
)
def display_name(user):
    if user:
        if user['status'] == 'admin':
            opts = opt_list([2, 3, 4, 5, 6])
        else:
            opts = [{'label': v, 'value': v, 'disabled': True if v > 4 else False, 'title': f'select_n_{v}'}
                    for v in [2, 3, 4, 5, 6]]
        header = 'waiting for action'
        des_headers, des_values = None, None
        jobs = [v for v in user['Jobs'] if v['status'] == 2]
        if jobs:
            job = jobs[0]
            mode = job['mode']
            header = f'currently working: {mode_names[mode]}'
            des_headers, des_values = job_description(job)
        return [opts, opt_list(user['Agents']), des_headers, des_values, header] \
            + [False] * len(mode_names_disabled) + [user['status'] != 'admin']
    return [NUP, [], None, None, 'waiting for action'] + [True] * (len(mode_names_disabled) + 1)


@app.callback(
    Output('user_profile', 'data'), Output('logs', 'data'), Output('login_open', 'children'),
    Input('quit', 'n_clicks')
)
def login_quit(n):
    if n:
        return None, [], 'Log in'
    raise PreventUpdate


# Manage users
@app.callback(
    Output('users_name', 'options'), Output('alert', 'children'),
    Input('users', 'hidden')
)
def username_options(hidden):
    if hidden:
        raise PreventUpdate
    body = {
        'kind': 'name'
    }
    resp, content = api_request('POST', 'all_items', body)
    if resp == Resp.GOOD:
        return opt_list(content), NUP
    return [], general_alert(content)


@app.callback(
    Output('users_change', 'options'), Output('users_change', 'value'), Output('user_description', 'children'),
    Output('alert', 'children'),
    Input('users_name', 'value')
)
def user_status(name):
    if name:
        body = {
            'job': 'user_description',
            'name': name,
        }
        resp, content = api_request('POST', 'admin', body)
        if resp == Resp.GOOD:
            return opt_list(content['list']), content['status'], description_user(content['description']), NUP
        return [], None, None, general_alert(content)
    return [], None, None, NUP


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
def delete_users(n, name, options):
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
    Output('files_name', 'options'), Output('files_name', 'value'),
    Output('alert', 'children'), Output('files_weights', 'style'),
    Input('files_kind', 'value'),
    State('user_profile', 'data')
)
def files_options(kind, user):
    if kind and user:
        see_weights = 'visible' if kind == 'Agents' else 'hidden'
        if user['status'] == 'admin':
            body = {
                'kind': kind
            }
            resp, content = api_request('POST', 'all_items', body)
            if resp == Resp.GOOD:
                return opt_list(content), None, NUP, {'visibility': see_weights}
            return NUP, NUP, general_alert(content), {'visibility': 'hidden'}
        return opt_list(user[kind]), None, NUP, {'visibility': see_weights}
    return [], None, NUP, NUP


@app.callback(
    Output('files_description', 'children'),
    Input('files_name', 'value'),
    State('files_kind', 'value'), State('user_profile', 'data')
)
def files_show_description(idx, kind, user):
    if idx and user:
        return description_files(user, kind, idx)


@app.callback(
    Output('download', 'data'), Output('alert', 'children'), Output('api_update', 'n_intervals'),
    Output('files_kind', 'value'),
    Input('files_download', 'n_clicks'), Input('files_delete', 'n_clicks'), Input('files_weights', 'n_clicks'),
    State('files_kind', 'value'), State('files_name', 'value'), State('user_profile', 'data'),
    State('api_update', 'n_intervals')
)
def manage_files(n1, n2, n3, kind, idx, user, interval):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[1]
    if kind is None or idx is None:
        return NUP, general_alert('Choose a file to perform action'), NUP, NUP
    if action == 'download':
        return download_json(user, kind, idx), NUP, NUP, NUP
    body = {
        'kind': kind,
        'idx': idx,
        'action': action
    }
    resp, content = api_request('POST', 'file', body)
    if resp == Resp.GOOD:
        if action == 'delete':
            return NUP, general_alert(f'{idx} was successfully deleted from {kind}', good=True), interval + 1, None
        status, to_send = get_from_url(content)
        if status == Resp.GOOD:
            return to_send, NUP, NUP, NUP
        return NUP, general_alert(status), NUP, NUP
    return NUP, general_alert(content), NUP, NUP


# Guide
@app.callback(
    Output('guide_body', 'children'),
    Input('guide_ui', 'n_clicks'), Input('guide_pd', 'n_clicks'), Input('guide_ps', 'n_clicks')
)
def guide_body(*args):
    ctx = callback_context
    if not ctx.triggered:
        return dcc.Markdown(guide_interface, dedent=False, link_target='_blanc', className='app-guide_content')
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


# Play yourself
@app.callback(
    Output('current_game_mode', 'data'), Output('gauge_group', 'hidden'), Output('play-yourself-group', 'hidden'),
    Output('what_game', 'children'), Output('game', 'hidden'), Output('instruction', 'is_open'),
    Output('show_instruction', 'data'), Output('move_delay', 'disabled'), Output('current_game', 'data'),
    Input('play_open', 'n_clicks'),
    State('show_instruction', 'data'), State('current_game', 'data')
)
def open_play_yourself(n, show_instruction, game):
    if n:
        if game['row'] == EMPTY_GAME['row']:
            game = GAME.new_game()
        return 'play', True, False, mode_names['play'], True, show_instruction, 0, True, game
    raise PreventUpdate


@app.callback(
    Output('game_board', 'children'),
    Input('current_game', 'data')
)
def draw_board(game):
    return display_game(game)


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


# Replay Game/ Watch Agent
@app.callback(
    Output('current_game_mode', 'data'), Output('what_game', 'children'), Output('game_header', 'children'),
    Output('game', 'hidden'), Output('watch_params', 'hidden'), Output('replay_params', 'hidden'),
    Output('move_delay', 'disabled'), Output('gauge_group', 'hidden'), Output('play-yourself-group', 'hidden'),
    Input('watch_open', 'n_clicks'), Input('replay_open', 'n_clicks')
)
def open_replay_watch(*args):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    mode = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[0]
    if mode == 'watch':
        return mode, mode_names['play'], 'choose agent', False, False, True, True, False, True
    return mode, mode_names['play'], 'choose game', False, True, False, True, False, True


@app.callback(
    Output('watch_p_agent', 'options'), Output('alert', 'children'),
    Input('watch_params', 'hidden')
)
def get_watch_options(hidden):
    if hidden:
        raise PreventUpdate
    body = {
        'kind': 'Agents'
    }
    resp, content = api_request('POST', 'all_items', body)
    if resp == Resp.GOOD:
        return opt_list(content + EXTRA_AGENTS), NUP
    return [], general_alert(content)


@app.callback(
    Output('replay_game', 'options'), Output('alert', 'children'),
    Input('replay_params', 'hidden')
)
def get_replay_options(hidden):
    if hidden:
        raise PreventUpdate
    body = {
        'kind': 'Games'
    }
    resp, content = api_request('POST', 'all_items', body)
    if resp == Resp.GOOD:
        return opt_list(content), NUP
    return [], general_alert(content)


@app.callback(
    Output('tmp_user', 'data'), Output('tmp_update', 'disabled'), Output('move_delay', 'disabled'),
    Output('current_game', 'data'), Output('moves_tiles', 'data'), Output('current_move', 'data'),
    Output('what_game', 'children'), Output('game', 'hidden'), Output('alert', 'children'),
    Output('loading_progress', 'className'),
    Input('game_go', 'n_clicks'),
    [State('current_game_mode', 'data'), State('finish_game', 'value'),
     State('tmp_user', 'data'), State('current_game', 'data')]
    + [State(f'watch_p_{p}', 'value') for p in AGENT_PARAMS['watch']],
    background=True,
    running=[
        (State('game_go', 'disabled'), True, False),
        (State('game_close', 'disabled'), True, False)
    ]
)
def go_agent(*args):
    mode = args[1]
    if args[0] and mode == 'watch':
        states = {v['id']: v['value'] for v in callback_context.states_list}
        params = {v: states[f'{mode}_p_{v}'] for v in AGENT_PARAMS['watch']}
        if None in params.values():
            return NUP, NUP, NUP, NUP, NUP, NUP, NUP, NUP, general_alert('Some parameters are missing or invalid'), NUP
        if states['finish_game'] == 'New game':
            game = GAME.new_game()
        else:
            game = states['current_game']
            if game['row'] == EMPTY_GAME['row']:
                game = GAME.new_game()
        name = f'tmp_{time_suffix()}'
        agent = params['agent']
        idx = f'{name}:{agent}'
        body = {
            'idx': idx,
            'status': 1,
            'creation_time': time_now(),
            'launch_time': None,
            'name': name,
            'mode': mode,
            'new_game': 1,
            'row': game['row'],
            'score': game['score'],
            'n_moves': game['n_moves'],
            'moves': [],
            'tiles': [],
            'current': states['tmp_user'],
            **params
        }
        resp, content = api_request('POST', 'slow', body)
        if resp == Resp.GOOD:
            count = 0
            while count < agent_load_timeout:
                body = {
                    'idx': idx,
                    'mode': 'check_agent_load'
                }
                resp, content = api_request('POST', 'watch', body)
                if resp == resp.GOOD:
                    moves_tiles = {
                        'moves': [],
                        'tiles': []
                    }
                    return idx, False, False, game, moves_tiles, 0, f'Watch Agent Play: {agent}', True, NUP, NUP
                time.sleep(1)
                count += 1
            return NUP, NUP, True, NUP, NUP, NUP, NUP, NUP, general_alert(f'Agent {agent} failed to load'), NUP
        return NUP, NUP, True, NUP, NUP, NUP, NUP, NUP, general_alert(content), NUP
    raise PreventUpdate


@app.callback(
    Output('tmp_update', 'disabled'),
    Input('current_game_mode', 'data')
)
def disable_temp_update(mode):
    if mode != 'watch':
        return True
    raise PreventUpdate


@app.callback(
    Output('moves_tiles', 'data'), Output('tmp_update', 'disabled'), Output('move_delay', 'disabled'),
    Output('alert', 'children'),
    Input('tmp_update', 'n_intervals'),
    State('tmp_user', 'data'), State('moves_tiles', 'data')
)
def get_moves(n, idx, moves_tiles):
    if n and idx:
        moves = moves_tiles['moves']
        body = {
            'idx': idx,
            'break': len(moves),
            'mode': 'get_moves'
        }
        resp, content = api_request('POST', 'watch', body)
        if resp == resp.GOOD:
            moves_tiles['moves'] += content['moves']
            moves_tiles['tiles'] += content['tiles']
            return moves_tiles, content['moves'] and content['moves'][-1] == -1, NUP, NUP
    raise PreventUpdate


@app.callback(
    Output('gauge_group', 'hidden'), Output('play-yourself-group', 'hidden'), Output('move_delay', 'disabled'),
    Output('current_game', 'data'), Output('moves_tiles', 'data'), Output('current_move', 'data'),
    Output('what_game', 'children'), Output('game', 'hidden'), Output('alert', 'children'),
    Input('game_go', 'n_clicks'),
    State('current_game_mode', 'data'), State('replay_game', 'value')
)
def go_replay(n, mode, idx):
    if n and mode == 'replay':
        if idx is None:
            return NUP, NUP, NUP, NUP, NUP, NUP, NUP, NUP, general_alert('Choose a Game to replay')
        body = {
            'idx': idx,
        }
        resp, content = api_request('POST', 'replay', body)
        if resp == Resp.GOOD:
            game = {
                'idx': content['idx'],
                'initial': content['initial'],
                'row': content['initial'],
                'score': 0,
                'n_moves': 0,
                'last_tile': [-1, -1],
                'next_move': content['moves'][0]
            }
            moves_tiles = {
                'moves': content['moves'],
                'tiles': content['tiles']
            }
            return False, True, False, game, moves_tiles, 0, f'Replay Game: {idx}', True, NUP
        return NUP, NUP, NUP, NUP, NUP, NUP, NUP, NUP, general_alert(content)
    raise PreventUpdate


@app.callback(
    Output('move_delay', 'disabled'), Output('current_game', 'data'), Output('moves_tiles', 'data'),
    Output('current_move', 'data'), Output('watch_open', 'n_clicks'), Output('alert', 'children'),
    Input('go_again', 'n_clicks'),
    State('current_game_mode', 'data'), State('tmp_user', 'data'),
    State('current_game', 'data'), State('moves_tiles', 'data'), State('watch_open', 'n_clicks')
)
def replay_watch_again(n, mode, tmp_user, game, moves_tiles, n_watch):
    if n:
        if mode == 'replay':
            if game is None or moves_tiles is None:
                return NUP, NUP, NUP, NUP, NUP, general_alert('Nothing to replay')
            replay = {
                'idx': game['idx'],
                'initial': game['initial'],
                'row': game['initial'],
                'score': 0,
                'n_moves': 0,
                'last_tile': [-1, -1],
                'next_move': moves_tiles['moves'][0]
            }
            return False, replay, moves_tiles, 0, NUP, NUP
        elif mode == 'watch':
            game = GAME.new_game()
            moves_tiles = {
                'moves': [],
                'tiles': []
            }
            body = {
                'idx': tmp_user,
                'mode': 'once_again',
                'row': game['row']
            }
            resp, content = api_request('POST', 'watch', body)
            if resp == Resp.GOOD:
                return False, game, moves_tiles, 0, NUP, NUP
            return NUP, NUP, NUP, NUP, n_watch + 1, general_alert(content)
    raise PreventUpdate


@app.callback(
    Output('gauge', 'value'), Output('move_delay', 'interval'),
    Input('gauge_slider', 'value')
)
def gauge_slider(value):
    return value, value * SPEED['step'] + SPEED['min']


@app.callback(
    Output('move_delay', 'disabled'),
    Input('pause_game', 'n_clicks')
)
def pause_game(n):
    return bool(n)


@app.callback(
    Output('move_delay', 'disabled'),
    Input('resume_game', 'n_clicks')
)
def resume_game(n):
    return not bool(n)


@app.callback(
    Output('go_again', 'disabled'),
    Input('move_delay', 'disabled')
)
def resume_game(pause):
    return not pause


@app.callback(
    Output('current_game', 'data'), Output('current_move', 'data'),
    Output('move_delay', 'disabled'), Output('tmp_update', 'disabled'),
    Input('move_delay', 'n_intervals'),
    State('moves_tiles', 'data'), State('current_move', 'data'),
    State('current_game', 'data'), State('current_game_mode', 'data')
)
def make_a_move_replay(n, moves_tiles, current_move, game, mode):
    if n and moves_tiles:
        moves = moves_tiles['moves']
        if not moves:
            return NUP, NUP, NUP, NUP
        tiles = moves_tiles['tiles']
        direction = moves[current_move]
        if direction == -1:
            return NUP, NUP, True, True
        new_game, change = GAME.make_move(game, direction)
        if current_move + 1 < len(moves):
            new_game['next_move'] = moves[current_move + 1]
        elif mode == 'watch':
            new_game['next_move'] = -1
        else:
            new_game['next_move'] = None
        GAME.place_tile(new_game, tiles[current_move])
        return new_game, current_move + 1, NUP, False
    raise PreventUpdate


# Agent pane
@app.callback(
    Output('current_agent_mode', 'data'), Output('agent_header', 'children'),
    Output('train_p_agent_ex', 'options'), Output('test_p_agent', 'options'),
    Output('agent', 'hidden'), Output('train_params', 'hidden'), Output('test_params', 'hidden'),
    Input('train_open', 'n_clicks'), Input('test_open', 'n_clicks'),
    State('user_profile', 'data')
)
def get_agent_params(n1, n2, user):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    mode = ctx.triggered[0]['prop_id'].split('.')[0].split('_')[0]
    match mode:
        case 'train':
            return mode, 'training parameters', opt_list(user['Agents']), NUP, False, False, True
        case 'test':
            return mode, 'testing parameters', NUP, agents_extra(user['Agents']), False, True, False


@app.callback(
    [Output('existing_visible', 'hidden'), Output('new_visible', 'hidden')]
    + [Output(f'train_p_{v}', 'value') for v in AGENT_PARAMS['train']]
    + [Output(f'train_p_{v}', 'disabled') for v in AGENT_TRAIN_LIST],
    Input('existing_new', 'value'),
    State('user_profile', 'data')
)
def populate_train_params(mode, user):
    if not user:
        raise PreventUpdate
    if mode == 'Existing Agent':
        return [False, True] \
            + [None for _ in AGENT_PARAMS['train']] \
            + [(True if v in ('n', ) else False) for v in AGENT_TRAIN_LIST]
    return [True, False] \
        + [None, None] + [AGENT_TRAIN_DEF[v] for v in AGENT_TRAIN_LIST] \
        + [False for _ in AGENT_TRAIN_LIST]


@app.callback(
    [Output(f'train_p_{v}', 'value') for v in AGENT_TRAIN_LIST],
    Input('train_p_agent_ex', 'value'),
    State('user_profile', 'data')
)
def toggle_training(idx, user):
    if idx:
        agent = [v for v in user['Agents'] if v['idx'] == idx][0]
        return [agent[v] for v in AGENT_TRAIN_LIST[:-1]] + [AGENT_TRAIN_DEF['episodes']]
    raise PreventUpdate


@app.callback(
    Output('agent', 'hidden'), Output('api_update', 'n_intervals'), Output('alert', 'children'),
    Input('agent_btn', 'n_clicks'),
    [State('current_agent_mode', 'data'), State('user_profile', 'data'),
     State('existing_new', 'value'), State('api_update', 'n_intervals')]
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
    is_new = (mode == 'train') and (states['existing_new'] == 'New Agent')
    if mode == 'train':
        agent = states['train_p_agent_new'] if is_new else states['train_p_agent_ex']
        params = {v: states[f'{mode}_p_{v}'] for v in AGENT_TRAIN_LIST}
        if params['n'] is not None:
            params['n'] = int(params['n'])
    else:
        agent = states['test_p_agent']
        params = {v: states[f'{mode}_p_{v}'] for v in AGENT_TEST_LIST}
    if agent is None or None in params.values():
        return NUP, NUP, general_alert('Some parameters are missing or invalid')
    if (agent not in EXTRA_AGENTS) and is_bad_name(agent):
        return NUP, NUP, general_alert('Agent name can contain only literals, numbers and "_" symbol, '
                                       'and be at most 12 symbols long')
    name = user['name']
    idx = f'{name}:{mode}:{agent}:{time_suffix()}'
    body = {
        'idx': idx,
        'status': 1,
        'creation_time': time_now(),
        'launch_time': None,
        'name': name,
        'mode': mode,
        'is_new': is_new,
        'agent': agent,
        **params
    }
    resp, content = api_request('POST', 'slow', body)
    if resp == Resp.GOOD:
        return True, states['api_update'] + 1, general_alert(f'{idx} is in queue, {content} jobs ahead', good=True)
    else:
        return NUP, NUP, general_alert(content)


@app.callback(
    Output('alert', 'children'),
    Input('stop_job', 'n_clicks'), Input('kill_job', 'n_clicks'),
    State('user_profile', 'data')
)
def stop_job(*args):
    ctx = callback_context
    user = args[-1]
    if not ctx.triggered or not user:
        raise PreventUpdate
    new_status = 0 if ctx.triggered[0]['prop_id'].split('.')[0] == 'stop_job' else -1
    jobs = user['Jobs']
    if not jobs:
        raise PreventUpdate
    idx = jobs[0]['idx']
    body = {
        'idx': idx,
        'status': new_status
    }
    resp, content = api_request('POST', 'job_status', body)
    if resp == Resp.GOOD:
        return general_alert(f'{job_status_description[new_status]} {idx} request received', good=True)
    else:
        return general_alert(content)


# Chart training history
@app.callback(
    Output('chart_open', 'disabled'),
    Input('test_p_agent', 'value')
)
def enable_chart_button(idx):
    return not bool(idx)


@app.callback(
    Output('chart_body', 'children'),
    Input('chart_open', 'n_clicks'),
    State('test_p_agent', 'value'), State('user_profile', 'data')
)
def train_history_chart(n, idx, user):
    if n:
        agent = get_array_item(user, 'Agents', idx)
        step = agent['collect_step']
        y = agent['train_history']
        x = list(range(step, step * len(y) + 1, step))
        return dcc.Graph(figure={
                'data': [{'x': x, 'y': y, 'type': 'line'}],
                'layout': {
                    'title': f"{agent['idx']} training history over {step * len(y)} episodes",
                    'xaxis': {'title': 'Training episode'},
                    'yaxis': {'title': 'Average score over 100 games'}
                }
            }, responsive=True)
    raise PreventUpdate


for v in divs_draggable:
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
