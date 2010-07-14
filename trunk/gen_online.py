#!/usr/bin/env python

import rrdtool , time , random, calendar

start_time = '2010-06-01 00:00'
start_time = time.strptime(start_time, "%Y-%m-%d %H:%M")
start_time = int(time.mktime(start_time))


fname = 'stc_online.rrd'

rrdtool.create(fname,
        '--start', str(start_time),
        '--step', '60',
        'DS:online:GAUGE:60:0:U',
        'RRA:LAST:0.5:1:1576800'
)

def round(timestamp):
    reminder = timestamp % 60
    timestamp = timestamp - reminder
    if reminder > 30:
        timestamp = timestamp + 60
    return timestamp

def get_rounded_timestamp(date_string):
    log_date = time.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    log_date = int(time.mktime(log_date))
    return round(log_date)

f = file("reports.log")
for l in f:
    log_date = get_rounded_timestamp(l[0:19]) + 60*60*8
    data = eval(l[29:-1].strip())
    s = '%d:%d' % (log_date, data["STCOnlineUsers"])
    try:
        rrdtool.update(fname , s)
    except:
        print l