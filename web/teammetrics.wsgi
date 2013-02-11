#!/usr/bin/python

import sys
import logging

logging.basicConfig(stream=sys.stderr)

sys.path.insert(0,"/var/lib/teammetrics/")

from web.teammetrics import app as application
