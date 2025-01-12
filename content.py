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
import websys

import config

LOCK_FILE_PATH = 'lock'
LOG_DIR = '../private/logs/contents/'
LOG_MAX = 1000

FILE_TYPES = {
    'accdb': {'mime': 'application/msaccess', 'download': True},
    'avif': {'mime': 'image/avif', 'download': True},
    'bmp': {'mime': 'image/bmp', 'download': False},
    'cab': {'mime': 'application/vnd.ms-cab-compressed', 'download': True},
    'class': {'mime': 'application/octet-stream', 'download': True},
    'cur': {'mime': 'image/vnd.microsoft.icon', 'download': True},
    'elf': {'mime': 'application/octet-stream', 'download': True},
    'eps': {'mime': 'application/postscript', 'download': True},
    'exe': {'mime': 'application/x-msdownload', 'download': True},
    'gif': {'mime': 'image/gif', 'download': False},
    'gz': {'mime': 'application/gzip', 'download': True},
    'html': {'mime': 'text/html', 'download': False},
    'ico': {'mime': 'image/x-icon', 'download': False},
    'jpg': {'mime': 'image/jpeg', 'download': False},
    'lzh': {'mime': 'application/octet-stream', 'download': True},
    'mid': {'mime': 'audio/midi', 'download': True},
    'mov': {'mime': 'video/quicktime', 'download': True},
    'mp3': {'mime': 'audio/mpeg', 'download': True},
    'mp4': {'mime': 'video/mp4', 'download': True},
    'mpg': {'mime': 'video/mpeg', 'download': True},
    'ole2': {'mime': 'application/octet-stream', 'download': True},
    'pdf': {'mime': 'application/pdf', 'download': False},
    'png': {'mime': 'image/png', 'download': False},
    'svg': {'mime': 'image/svg+xml', 'download': False},
    'txt': {'mime': 'plain/text', 'download': False},
    'wav': {'mime': 'audio/wav', 'download': True},
    'webp': {'mime': 'image/webp', 'download': False},
    'xml': {'mime': 'text/xml', 'download': True},
    'zip': {'mime': 'application/x-zip-compressed'},
    'xlsx': {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'download': True},
    'docx': {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'download': True},
    'pptx': {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'download': True},
    'war': {'mime': 'application/x-zip', 'download': True},
    'jar': {'mime': 'application/java-archive', 'download': True}
}

#------------------------------------------------------------------------------
def get_file_type(content_path):
    ext = util.get_file_ext(content_path)
    type = {'mime': 'application/octet-stream'}
    if ext in FILE_TYPES:
        type = FILE_TYPES[ext]
    return type

#------------------------------------------------------------------------------
def send_content(context, content_root, content_path, content_priv, q, log_path):
    info = omit_file_param(q)
    content = None

    if content_priv != '' and not context.has_permission(content_priv):
        status = 'FORBIDDEN'
        info = status + ' ' + info
        write_log(context, log_path, content_path, content, info)
        send_error(status)
        return False

    file_path = content_root + content_path
    if not util.path_exists(file_path):
        status = 'READ_ERROR'
        info = status + ' ' + info
        write_log(context, log_path, content_path, content, info)
        send_error(status)
        return False

    content = util.read_binary_file(file_path)
    write_log(context, log_path, content_path, content, info)
    type = get_file_type(content_path)
    mime = type['mime']
    content_len = len(content)
    headers = [{'Content-Length': str(content_len)}]

    if type['download']:
        filename = util.get_filename(content_path)
        headers.append({'Content-Disposition': 'attachment;filename="' + filename + '"'})

    websys.send_response(content, mime, headers)

#------------------------------------------------------------------------------
def send_error(s):
    websys.send_response(s, 'text/plain')

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
    html = '''<html>
<head>
<title>Log</title>
<style>
body {
  font-size: 13px;
  font-family: Consolas, Monaco, Menlo, monospace, sans-serif;
}
table {
  border-collapse: collapse;
  font-size: 13px;
}
td {
  padding: 0;
  padding-right: 24px;
  white-space: pre;
}
</style>
</head>
<body>
<table>
'''

    for i in range(len(log_list)):
        l = log_list[i]
        logs = l.split('\t')
        date_time = logs[0]
        path = logs[1]
        s_content_len = logs[2]
        sid = logs[3]
        user = util.escape_xml(logs[4])
        addr = logs[5]
        host = logs[6]
        brows = logs[7]
        info = logs[8]

        html += '<tr>'
        html += '<td>' + date_time + '</td>'
        html += '<td>' + path + '</td>'
        html += '<td>' + s_content_len + '</td>'
        html += '<td>' + sid + '</td>'
        html += '<td>' + user + '</td>'
        html += '<td>' + addr + '</td>'
        html += '<td>' + host + '</td>'
        html += '<td>' + brows + '</td>'
        html += '<td>' + info + '</td>'
        html += '</tr>'

    html += '<table></body></html>'
    websys.send_response(html, 'text/html')

def omit_file_param(q):
    q = util.replace(q, 'file=[^&]+', '')
    q = util.replace(q, '^&', '')
    q = util.replace(q, '&$', '')
    q = util.replace(q, '&&', '&')
    return q

#------------------------------------------------------------------------------
def write_log(context, log_path, path, content, info):
    uid = context.get_user_id()
    if should_exclude_logging(uid):
        return

    now = util.get_timestamp()
    date_time = util.get_datetime_str(now, fmt='%Y-%m-%dT%H:%M:%S.%f')
    sid = get_session_id(context)
    user = get_user_name(context)
    addr = util.get_ip_addr()
    host = util.get_host_name()
    ua = util.get_user_agent()
    brows = util.get_browser_short_name(ua)
    s_content_len = ''
    if content is not None:
        content_len = len(content)
        s_content_len = util.format_number(content_len) + ' bytes'

    text_list = [
        date_time,
        path,
        s_content_len,
        sid,
        user,
        addr,
        host,
        brows,
        info
    ]
    logtxt = build_log_text(text_list)

    write_log_to_file(log_path, logtxt)

def should_exclude_logging(uid):
    exclude_uids = config.exclude_logging_uids
    for i in range(len(exclude_uids)):
        id = exclude_uids[i]
        if id == uid:
            return True
    return False

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
        ts = context.get_timestamp()
        user_name = '<Anonymous>'
        if ts is not None:
            user_name += str(ts)
    return user_name

def is_allowed_path(content_path, allow_content_paths):
    for i in range(len(allow_content_paths)):
        path = allow_content_paths[i]
        if content_path == path:
            return True
    return False

#------------------------------------------------------------------------------
def build_auth_redirection_screen(root_path):
    html = '<!DOCTYPE html>'
    html += '<html>'
    html += '<head>'
    html += '<meta charset="utf-8">'
    html += '<script src="' + root_path + 'libs/util.js"></script>'
    html += '<script src="' + root_path + 'websys/websys.js"></script>'
    html += '<script>'
    html += 'websys.init(\'' + root_path + '\');'
    html += '$onLoad = function() {websys.authRedirection(location.href);};'
    html += '</script>'
    html += '</head>'
    html += '<body></body>'
    html += '</html>'
    return html

#------------------------------------------------------------------------------
def main(settings):
    websys.init(http_encryption=False)
    context = websys.on_access()

    root_path = settings['root_path']
    base_path = settings['base_path']
    default_content_path = settings['default_content_path']
    allow_content_paths = settings['allow_content_paths']
    content_priv = settings['content_priv']
    log_file_name = settings['log_file_name']
    log_view_priv = settings['log_view_priv']

    if content_priv != '' and not context.is_authorized():
        html = build_auth_redirection_screen(root_path)
        util.send_html(html)
        return

    log_path = root_path + LOG_DIR + log_file_name + '.log'

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

    file = util.get_request_param('file')
    if file is None:
        content_path = default_content_path
    else:
        if is_allowed_path(file, allow_content_paths):
            content_path = file
        else:
            send_error('NOT_IN_LIST')
            return

    content_root = ''
    if base_path != '':
        content_root = base_path
        content_root = util.replace(content_root, '%ROOT_PATH%', root_path)

    send_content(context, content_root, content_path, content_priv, q, log_path)
