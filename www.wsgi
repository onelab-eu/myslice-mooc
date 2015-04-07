#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)

sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))

from myops2 import app as application