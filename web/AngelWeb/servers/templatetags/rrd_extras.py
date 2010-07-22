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
    result = str(rrd_data[2][0][0])
    if result.endswith(".0"):
        return result[:-2]
    return result

def check_date(info, thred = 3):
    last_update = info["last_update"]
    import time
    past = time.time() - last_update
    result = ""
    if past > (thred * 60):
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
    thred = 3
    
    if len(widget.data_def) > 0:
        try:
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            thred = data_def["interval"]
        except:
            pass

    return widget.title + check_date(info, thred)
    
def show_int(value):
    return str(int(value))

def show_percent(value):
    return str(value * 100) + "%"

@register.filter(name='show_widget_with_current_value')
def show_widget_with_current_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = str(info["last_update"])
    
    current = rrdtool.fetch(rrd_path, "-s", last_update + "-1", "-e", "s+0", "LAST")
    
    if len(widget.data_def) > 0:
        try:
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
        except:
            return widget.data_def
    
        data = list(current[2][0])
        ds = current[1]
        for i in range(0, len(ds)):
            if data_def.has_key(ds[i]):
                cmd = data_def[ds[i]][0]
                data[i] = eval(cmd + "(" + str(data[i])  + ")")
            else:
                data[i] = str(data[i])
    else:
        data = map(str, current[2][0])
    
    #return check_date(info) + get_last_value(current) + "</td>"
    
    return "<td>" + "</td><td>".join(data) + "</td>"

@register.filter(name='show_widget_with_current_and_past_value')
def show_widget_with_current_and_past_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    #last_update = datetime.datetime.fromtimestamp(info["last_update"]).strftime("%m-%d %H:%M")
    last_update = str(info["last_update"])
    
    current = rrdtool.fetch(rrd_path, "-s", last_update + "-1", "-e", "s+0", "LAST")  
    yesterday = rrdtool.fetch(rrd_path, "-s", last_update + "-1d", "-e", "s+1", "LAST")
    lastweek = rrdtool.fetch(rrd_path, "-s", last_update + "-1w", "-e", "s+1", "LAST")
    
    return "<td>" + "</td><td>".join([get_last_value(current), get_last_value(yesterday) , get_last_value(lastweek)]) + "</td>"