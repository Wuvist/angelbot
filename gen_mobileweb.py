#!/usr/bin/env python

import rrdtool , time , random, calendar

start_time = '2010-06-17 00:00'
start_time = time.strptime(start_time, "%Y-%m-%d %H:%M")
start_time = int(time.mktime(start_time))


fname = 'mobileweb.rrd'

rrdtool.create(fname,
        '--start', str(start_time),
        '--step', '60',
        'DS:delivery_rate:GAUGE:60:0:U',
        'DS:load:GAUGE:60:0:U',
        'DS:speed:GAUGE:60:0:U',
        'DS:rps:GAUGE:60:0:U',
        'RRA:LAST:0.5:1:1576800'
)

def round(timestamp):
    reminder = timestamp % 60
    timestamp = timestamp - reminder
    if reminder > 30:
        timestamp = timestamp + 60
    return timestamp

for i in range(18, 30):
    f = file("iis/2010-06-" + str(i) + ".log")
    for l in f:
        data = eval(l[:-1].strip())
        s = '%d:%f:%d:%d:%d' % (round(data["modified_on"]), data["ok"] /float(1000), data["cpu"], data["avg_time"], data["requests"])
        rrdtool.update(fname , s)