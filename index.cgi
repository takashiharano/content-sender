#!python
#!/usr/bin/python3
#==============================================================================
# Content Sender
#------------------------------------------------------------------------------
ROOT_PATH = '../../'

CONTENT_DIR = ''
CONTENT_FILE = 'test.pdf'

LOG_VIEW_PRIV = 'xxxadmin'

#------------------------------------------------------------------------------
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util

util.append_system_path(__file__, ROOT_PATH + 'content')
import content

CONTENT_PATH = CONTENT_DIR + CONTENT_FILE

content.main(ROOT_PATH, CONTENT_PATH, LOG_VIEW_PRIV)
