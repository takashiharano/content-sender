#!python
#!/usr/bin/python3
#==============================================================================
# Content Sender
#------------------------------------------------------------------------------
settings = {
    'root_path': '../../',
    'base_path': '../private/content1/a/',
    'default_content_path': 'test.pdf',
    'allow_content_paths': ['test.pdf', 'b/test2.pdf'],
    'content_priv': 'p1',
    'log_file_name': 'test',
    'log_view_priv': 'xxxadmin'
}
#------------------------------------------------------------------------------
import os
import sys
ROOT_PATH = settings['root_path']
sys.path.append(os.path.join(os.path.dirname(__file__), ROOT_PATH + 'libs'))
import util
util.append_system_path(__file__, ROOT_PATH + 'content')
import content
content.main(settings)
