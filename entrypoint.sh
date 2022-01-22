#!/bin/sh
cat $GITHUB_EVENT_PATH
/usr/bin/python3 /goscana.py "$@"
