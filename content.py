#==============================================================================
# Content Sender
# Copyright (c) 2024 Takashi Harano
# Released under the MIT license
#==============================================================================
import os
import sys

ROOT_PATH = '../'
sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH + 'websys')
import web

LOCK_FILE_PATH = 'lock'
LOG_DIR = '../private/logs/contents/'
LOG_MAX = 1000

#------------------------------------------------------------------------------
def send_content(context, content_path, mime, q, log_path):
    content = util.read_binary_file(content_path)
    write_log(context, content_path, content, q, log_path)
    content_len = len(content)
    headers = [{'Content-Length': str(content_len)}]
    web.send_response(content, mime, headers)

#------------------------------------------------------------------------------
def synchronize_start():
    if util.file_lock(LOCK_FILE_PATH, 15, 0.2):
        return True
    return False

def synchronize_end():
    util.file_unlock(LOCK_FILE_PATH)

#------------------------------------------------------------------------------
def view_log(context, log_path, n, log_view_priv):
    if not context.has_permission(log_view_priv):
        send_error('FORBIDDEN')
        return False

    log_list = get_log(log_path)
    if n > 0:
        n = n * (-1)
        log_list = log_list[n:]

    send_log(log_list)

    return True

def get_log(log_path):
    return util.read_text_file_as_list(log_path)

def send_log(log_list):
    s = util.align_by_tab(log_list)
    web.send_response(s, 'text/plain')

#------------------------------------------------------------------------------
def write_log(context, path, content, q, log_path):
    now = util.get_timestamp()
    date_time = util.get_datetime_str(now, fmt='%Y-%m-%dT%H:%M:%S.%f')
    sid = get_session_id(context)
    user = get_user_name(context)
    addr = util.get_ip_addr()
    host = util.get_host_name()
    ua = util.get_user_agent()
    brows = util.get_browser_short_name(ua)
    content_len = len(content)

    text_list = [
        date_time,
        path,
        str(content_len) + ' bytes',
        sid,
        user,
        addr,
        host,
        brows,
        q
    ]
    logtxt = build_log_text(text_list)

    write_log_to_file(log_path, logtxt)

def build_log_text(text_list):
    s = ''
    for i in range(len(text_list)):
        txt = text_list[i]
        if i > 0:
            s += '\t'
        s += txt
    return s

def write_log_to_file(log_path, logtxt):
    if synchronize_start():
        util.append_line_to_text_file(log_path, logtxt, max=LOG_MAX)
        synchronize_end()

def get_session_id(context):
    sid = context.get_session_id()
    if sid is None:
        return '-'
    sid = sid[:7]
    return sid

def get_user_name(context):
    user_name = context.get_user_fullname()
    if user_name == '':
        user_name = '-'
    return user_name

def send_error(s):
    web.send_response(s, 'text/plain')

#------------------------------------------------------------------------------
def main(root_dir, content_path, mime, log_file, log_view_priv=None):
    log_path = root_dir + LOG_DIR + log_file
    web.init(http_encryption=False)
    context = web.on_access()

    q = util.get_query()
    log_n = util.get_request_param('log', q=q)
    if log_n is not None:
        n = 50
        try:
            n = int(log_n)
        except:
            pass

        view_log(context, log_path, n, log_view_priv)
        return

    send_content(context, content_path, mime, q, log_path)
