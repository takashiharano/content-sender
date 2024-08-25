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

MIME_TYPE = {
    'accdb': 'application/msaccess',
    'avif': 'image/avif',
    'bmp': 'image/bmp',
    'cab': 'application/vnd.ms-cab-compressed',
    'class': 'application/octet-stream',
    'cur': 'image/vnd.microsoft.icon',
    'elf': 'application/octet-stream',
    'eps': 'application/postscript',
    'exe': 'application/x-msdownload',
    'gif': 'image/gif',
    'gz': 'application/gzip',
    'html': 'text/html',
    'ico': 'image/x-icon',
    'jpg': 'image/jpeg',
    'lzh': 'application/octet-stream',
    'mid': 'audio/midi',
    'mov': 'video/quicktime',
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4',
    'mpg': 'video/mpeg',
    'ole2': 'application/octet-stream',
    'pdf': 'application/pdf',
    'png': 'image/png',
    'svg': 'image/svg+xml',
    'txt': 'plain/text',
    'wav': 'audio/wav',
    'webp': 'image/webp',
    'xml': 'text/xml',
    'zip': 'application/x-zip-compressed',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'war': 'application/x-zip',
    'jar': 'application/java-archive'
}

#------------------------------------------------------------------------------
def get_mime_type(content_path):
    ext = util.get_file_ext(content_path)
    mime = MIME_TYPE[ext]
    return mime

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
    mime = get_mime_type(content_path)
    content_len = len(content)
    headers = [{'Content-Length': str(content_len)}]
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

    content_path = default_content_path

    file = util.get_request_param('file')
    if file is not None:
        content_path = None
        if is_allowed_path(file, allow_content_paths):
            content_path = file

    if content_path is None:
        send_error('NOT_FOUND')
        return

    content_root = ''
    if base_path != '':
        content_root = base_path
        content_root = util.replace(content_root, '%ROOT_PATH%', root_path)

    send_content(context, content_root, content_path, content_priv, q, log_path)
