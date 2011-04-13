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

def get_last_value(rrd_data, field_def = None):
    if field_def:
        return format_value(field_def, rrd_data[2][0][0], False)
    result = str(rrd_data[2][0][0])
    if result.endswith(".0"):
        return result[:-2]
    return result

def format_value(field_def, value, check_values = True):
    cmd = field_def[0]
    is_error = False
    is_warning = False
    
    if value != None:
        is_warning = eval(str(value) + field_def[1])
        if is_warning:
            is_error = eval(str(value) + field_def[2])
    result = eval(cmd + "(" + str(value)  + ")")

    if is_error and check_values:
        result = "<div class='errornote'>" + result + "</div>"
    elif is_warning and check_values:
        result = "<div class='errors'>" + result + "</div>"

    return result

def format_value_def(field_def,data_rrd):
    if data_rrd[-1] == None or False in [eval(str(x)+field_def[2]) for x in data_rrd if x != None ]:
        try:
            if data_rrd[-1] ==None or eval(str(data_rrd[-1])+ field_def[1]):
                result = "<div class='errors'>" + eval(field_def[0]+"("+str(data_rrd[-1])+")") + "</div>"
            else:
                result = eval(field_def[0]+"("+str(data_rrd[-1])+")")
        except:
            result = str(field_def)
            #result = eval(field_def[0]+"("+str(data_rrd[-1])+")") #never errors
    else:
        result = "<div class='errornote'>" + eval(field_def[0]+"("+str(data_rrd[-1])+")") + "</div>"
        
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
    
    if widget.data_def:
        try:
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            thred = data_def["interval"]
        except:
            pass

    return widget.title + check_date(info, thred)
    
def show_int(value):
    if value:
        return str(int(value))
    return "None"

def show_float(value):
    if value:
        return "%.2f" % value
    return "None"

def show_ok(value):
    if not value:
        return "OK"
    return "Error"

def show_percent(value):
    if value:
        return "%.2f" % (value * 100) + " %"
    else:
        return "None"

@register.filter(name='show_widget_with_current_value')
def show_widget_with_current_value(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = str(info["last_update"])
    
    current = rrdtool.fetch(rrd_path, "-s", last_update + "-1", "-e", "s+0", "LAST")
    
    if widget.data_def:
        try:
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            data = list(current[2][0])
            ds = current[1]
            for i in range(0, len(ds)):
                if data_def.has_key(ds[i]):
                    field_def = data_def[ds[i]]
                    try:
                        data_rrd = rrdtool.fetch(rrd_path, "-s", str(int(last_update)-int(field_def[3]) * 60), "-e", last_update + "-1", "LAST")
                        data_rrd = map(lambda x:x[i],data_rrd[2])
                        data[i] = format_value_def(field_def,data_rrd)
                    except:
                        data[i] = format_value(field_def, data[i])
                else:
                    data[i] = str(data[i])
        except:
            return widget.data_def
            #raise
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
    
    current_value = current[2][0][0]
    field_def = None
    if widget.data_def:
        try:
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            ds = (current[1][0])
            if data_def.has_key(ds):
                field_def = data_def[ds]
                try:
                    data_rrd = rrdtool.fetch(rrd_path, "-s", str(int(last_update)-int(field_def[3]) * 60), "-e", last_update + "-1", "LAST")
                    data_rrd = map(lambda x:x[0],data_rrd[2])
                    current_value = format_value_def(field_def,data_rrd)
                except:
                    current_value = format_value(field_def, current_value)
            else:
                current_value = get_last_value(current)
        except:
            raise
            return widget.data_def
    else:
        current_value = get_last_value(current)
    
    return "<td>" + "</td><td>".join([current_value, get_last_value(yesterday, field_def) , get_last_value(lastweek, field_def)]) + "</td>"