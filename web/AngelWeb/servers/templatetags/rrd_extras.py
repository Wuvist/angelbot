import os
from django import template
from django.conf import settings
import rrdtool
import datetime

register = template.Library()


@register.filter(name='show_rrd')
def show_rrd(rrd):
    "Format a rrd object in HTML"
    if os.access(rrd.path(), os.F_OK):
        return " "
    
    return "<a href='/rrd/%d/create'>Create</a>" % rrd.id
    
@register.filter(name='get_widget_img_src')
def get_widget_img_src(widget, width, height):
    "Format a rrd object in HTML"
    cmd = rrd.graph_def.replace("\n", "").replace("\r", " ")
    cmd = cmd.replace("{rrd}", widget.rrd.name).replace("{height}", str(height)).replace("{width}", str(width))

    return cmd

def get_last_value(rrd_data):
    return str(rrd_data[2][0][0])

def check_date(info):
    last_update = info["last_update"]
    import time
    past = time.time() - last_update
    result = ""
    if past > 180:
        #        result += "<div class='errors'>No update for 3 mins</div>"
        result = "<div class='errornote'>No update</div>"
    return result

@register.filter(name='show_widget_header')
def show_widget_header(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = str(info["last_update"])

    current = rrdtool.fetch(rrd_path, "-s", last_update, "-e", "s+1", "LAST")
    titles = map(lambda x: x.replace("_", " "), current[1])
    return "<th>" + "</th><th>".join(titles) + "</th>"

@register.filter(name='show_widget_title')
def show_widget_title(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)

    return widget.title + check_date(info)

@register.filter(name='show_widget_with_current_value')
def show_widget_with_current_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = str(info["last_update"])
    
    current = rrdtool.fetch(rrd_path, "-s", last_update, "-e", "s+1", "LAST")  
    #return check_date(info) + get_last_value(current) + "</td>"
    
    return "<td>" + "</td><td>".join(map(str, current[2][0])) + "</td>"

@register.filter(name='show_widget_with_current_and_past_value')
def show_widget_with_current_and_past_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    #last_update = datetime.datetime.fromtimestamp(info["last_update"]).strftime("%m-%d %H:%M")
    last_update = str(info["last_update"])
    
    current = rrdtool.fetch(rrd_path, "-s", last_update, "-e", "s+1", "LAST")
    yesterday = rrdtool.fetch(rrd_path, "-s", last_update + "-1d", "-e", "s+1", "LAST")
    lastweek = rrdtool.fetch(rrd_path, "-s", last_update + "-1w", "-e", "s+1", "LAST")
    
    return "<td>" + "</td><td>".join([get_last_value(current), get_last_value(yesterday) , get_last_value(lastweek)]) + "</td>"