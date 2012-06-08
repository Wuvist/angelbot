from django import template
from django.conf import settings
from cmdb.models import *
from servers.models import Widget as s_service
import datetime
register = template.Library()

@register.filter(name='showServerInfo')
def showServerInfo(id):
    '''Show server info'''
    try:
        s = Server.objects.get(server_id=id)
        result = "[%s: %s-%s-%s]" % (s.name,s.core,s.ram,s.hard_disk)
    except:
        result = ""
        
    return result

@register.filter(name='tr_color')
def tr_color(row_number):
    '''decide <tr> color'''
    if row_number % 2 == 0:
        return True
    else:
        return False
    
@register.filter(name='getLoad')
def getLoad(server_id):
    ''' get server load'''
    import rrdtool
    try:
        widget = Service.objects.get(server_id = server_id,title__contains = "perfmon")
        rrdPath = s_service.objects.get(id = widget.service_id).rrd.path()
    except:
        return ""
    
    info = rrdtool.info(rrdPath)
    last_update = str(info["last_update"])
    current = rrdtool.fetch(rrdPath, "-s", last_update + "-1", "-e", "s+0", "LAST")
    load = ""
    for i in range(len(current[1])):
        if current[1][i] == "load":
            load = current[2][0][i]
    if load == "nan":load = ""
    try:
        load = int(load)
    except:
        pass
    return load

@register.filter(name='getLoadWeek')
def getLoadWeek(server_id):
    ''' get server current load and one week load'''
    import rrdtool
    try:
        widget = Service.objects.get(server_id = server_id,title__contains = "perfmon")
        rrdPath = s_service.objects.get(id = widget.service_id).rrd.path()
    except:
        return "</td><td>"
    
    info = rrdtool.info(rrdPath)
    last_update = str(info["last_update"])
    current = rrdtool.fetch(rrdPath, "-s", last_update + "-604801", "-e", last_update + "-1", "LAST")
    load = "";ls = [];loadAvg = ""
    for i in range(len(current[1])):
        if current[1][i] == "load":
            load = current[2][-1][i]
            for l in current[2]:
                if l[i] != None and l[i] != "nan":ls.append(l[i])
    if load == "nan":load = ""
    try:
        load = int(load)
    except:
        pass
    if ls != []:
        loadAvg = int(sum(ls)/len(ls))
    return str(load)+"</td><td>"+str(loadAvg)
