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
    except:
        return ""
    
    rrdPath = s_service.objects.get(id = widget.service_id).rrd.path()
    info = rrdtool.info(rrdPath)
    last_update = str(info["last_update"])
    current = rrdtool.fetch(rrdPath, "-s", last_update + "-1", "-e", "s+0", "LAST")
    load = ""
    for i in range(len(current[1])):
        if current[1][i] == "load":
            load = current[2][0][i]
    if load == "nan":load = ""
    
    return load
