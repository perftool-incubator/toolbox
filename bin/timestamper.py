#!/usr/bin/python3

import time
import datetime

from datetime import timezone
from sys import stdin

def format_timestamp(ts):
    return format_datetime(datetime.datetime.fromtimestamp(ts, timezone.utc))

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f %Z")

for line in stdin:
    now = time.time()
    print(format_timestamp(now) + "|" + line, end='')
