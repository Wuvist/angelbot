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



@register.filter(name='show_widget_with_current_value')
def show_widget_with_current_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = datetime.datetime.fromtimestamp(info["last_update"]).strftime("%m-%d %H:%M")
    values = []
    for key in info.keys():
        if key.endswith(".last_ds"):
            values.append(info[key])
    
    return last_update + ": " + ",".join(values)


@register.filter(name='show_widget_with_current_and_past_value')
def show_widget_with_current_and_past_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = datetime.datetime.fromtimestamp(info["last_update"]).strftime("%m-%d %H:%M")
    
    yesterday = rrdtool.fetch(rrd_path, "-s", str(info["last_update"]) + "-1d-120", "-e", "s+1", "LAST")
    lastweek = rrdtool.fetch(rrd_path, "-s", str(info["last_update"]) + "-1w-10", "-e", "s+1", "LAST")
    
    values = []
    for key in info.keys():
        if key.endswith(".last_ds"):
            values.append(info[key])
    
    return str(info["last_update"]) + ": " + ",".join(values) + str(yesterday)+ str(lastweek)