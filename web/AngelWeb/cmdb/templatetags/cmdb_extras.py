from django import template
from django.conf import settings
from servers.models import Widget as s_service
import datetime
register = template.Library()

@register.filter(name='showServerInfo')
def showServerInfo(s):
    '''Show server info'''
    try:
        result = "[%s-%s-%s]" % (s.core,s.ram,s.hard_disk)
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
        rrdPath = s_service.objects.get(server__id = server_id,category__title__contains = "Perfmon").rrd.path()
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
        rrdPath = s_service.objects.get(server__id = server_id,category__title__contains = "Perfmon").rrd.path()
    except:
        return "</td><td>"
    
    info = rrdtool.info(rrdPath)
    last_update = str(info["last_update"])
    current = rrdtool.fetch(rrdPath, "-s", last_update + "-604801", "-e", last_update, "LAST")
    load = "";ls = [];loadAvg = ""
    for i in range(len(current[1])):
        if current[1][i] == "load":
            for l in current[2][-10:]:
                if l[i] != None and l[i] != "nan":
                    load = l[i]
            for l in current[2]:
                try:
                    ls.append(float(l[i]))
                except:
                    pass
    if load == "nan":load = ""
    try:
        load = int(load)
    except:
        pass
    if ls != []:
        loadAvg = str(sum(ls)/len(ls))[:5]
    return str(load)+"</td><td>"+loadAvg

@register.filter(name='showFunction')
def showFunction(n):
    from servers.models import SERVER_FUNCTION_CHOICES as tp
    dt = dict(tp)
    return dt[n]

@register.filter(name='showProjects')
def showProjects(s):
    return ",".join(s.project.all().values_list("name",flat=True))
