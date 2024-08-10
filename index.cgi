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

LOG_FILE = CONTENT_FILE + '.log'
LOG_VIEW_PRIV = 'xxxadmin'

#------------------------------------------------------------------------------
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH + 'websys/bin')
import web

util.append_system_path(__file__, ROOT_PATH + 'content')
import content

CONTENT_PATH = CONTENT_DIR + CONTENT_FILE

content.main(CONTENT_PATH, MIME, LOG_FILE, LOG_VIEW_PRIV)
