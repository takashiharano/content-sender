#!python
#!/usr/bin/python3
#==============================================================================
# Content Sender
# Copyright (c) 2024 Takashi Harano
# Released under the MIT license
#==============================================================================
ROOT_PATH = '../'

CONTENT_DIR = ''
CONTENT_FILE = 'test.pdf'
MIME = 'application/pdf'

LOG_DIR = ROOT_PATH + '../private/logs/contents/'
LOG_FILE = CONTENT_FILE + '.log'
LOG_PRIV = 'xxxadmin'

#------------------------------------------------------------------------------
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH)
util.append_system_path(__file__, ROOT_PATH + 'websys/bin')
import web

CONTENT_PATH = CONTENT_DIR + CONTENT_FILE
LOCK_FILE_PATH = 'lock'
LOG_FILE_PATH = LOG_DIR + LOG_FILE
LOG_MAX = 1000

#------------------------------------------------------------------------------
def send_content(context, q):
    content = util.read_binary_file(CONTENT_PATH)
    write_log(context, CONTENT_PATH, content, q)
    content_len = len(content)
    headers = [{'Content-Length': str(content_len)}]
    web.send_response(content, MIME, headers)

#------------------------------------------------------------------------------
def synchronize_start():
    if util.file_lock(LOCK_FILE_PATH, 15, 0.2):
        return True
    return False

def synchronize_end():
    util.file_unlock(LOCK_FILE_PATH)

#------------------------------------------------------------------------------
def view_log(context, q):
    if not context.has_permission(LOG_PRIV):
        return False

    n = 50
    log_n = util.get_request_param('log')
    if log_n is not None:
        try:
            n = int(log_n)
        except:
            pass
    elif q != 'log':
        return False

    log_list = get_log()
    if n > 0:
        n = n * (-1)
        log_list = log_list[n:]

    send_log(log_list)

    return True

def get_log():
    return util.read_text_file_as_list(LOG_FILE_PATH)

def send_log(log_list):
    s = ''
    for i in range(len(log_list)):
        s += log_list[i] + '\n'
    web.send_response(s, 'text/plain')

#------------------------------------------------------------------------------
def write_log(context, path, content, q):
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

    write_log_to_file(logtxt)

def build_log_text(text_list):
    s = ''
    for i in range(len(text_list)):
        txt = text_list[i]
        if i > 0:
            s += '\t'
        s += txt
    return s

def write_log_to_file(logtxt):
    if synchronize_start():
        util.append_line_to_text_file(LOG_FILE_PATH, logtxt, max=LOG_MAX)
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

#------------------------------------------------------------------------------
def main():
    web.init(http_encryption=False)
    context = web.on_access()

    q = util.get_query()
    if q != '':
        if view_log(context, q):
            return

    send_content(context, q)

main()
