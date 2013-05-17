from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Count 
from servers.models import *
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from datetime import datetime
from django.core.cache import cache
import time
import rrdtool

def show_int(value):
    if value == None:
        return "None"
    else:
        return str(int(value))
    return "None"

def show_float(value):
    if value == None:
        return "None"
    elif value or int(value) == 0:
        return "%.2f" % value
    return "None"

def show_ok(value):
    if not value:
        return "OK"
    return "Error"

def show_percent(value):
    if value or str(value) == "0":
        return "%.2f" % (value * 100) + " %"
    else:
        return "None"
def format_value(field_def, value, check_values = True):
    result = {"status":"ok"}
    cmd = field_def[0]
    is_error = False
    is_warning = False

    if value != None:
        is_warning = eval(str(value) + field_def[1])
        if is_warning:
            is_error = eval(str(value) + field_def[2])
    result["value"] = eval(cmd + "(" + str(value)  + ")")

    if is_error and check_values:
        result["status"] = "error"
    elif is_warning and check_values:
        result["status"] = "warning"

    return result

def format_value_def(field_def,data_rrd):
    result = {"status":"ok"}
    try:
        result["value"] = eval(field_def[0]+"("+str(data_rrd[-1])+")")
    except:
        result["value"] = str(data_rrd[-1])
    if data_rrd[-1] == None or False in [eval(str(x)+field_def[2]) for x in data_rrd if x != None ]:
        if (data_rrd[-1] != None) and (False not in [eval(str(x)+field_def[1]) for x in data_rrd if x != None ]):
            result["status"] = "warning"#"<div class='errors'>" + eval(field_def[0]+"("+str(data_rrd[-1])+")") + "</div>"
    else:
        result["status"] = "error"#"<div class='errornote'>" + eval(field_def[0]+"("+str(data_rrd[-1])+")") + "</div>"

    return result

def paser_widget(widget):
    rrd_path = widget.rrd.path()
    info = rrdtool.info(rrd_path)
    last_update = str(info["last_update"])

    current = rrdtool.fetch(rrd_path, "-s", last_update + "-1", "-e", "s+0", "LAST")
    result = {"widgetStatus":"ok","valueList":current[1],"widgetConfigDiff":False}
    if widget.data_def == None or widget.data_def != widget.data_default:
        result["widgetConfigDiff"] = True
    if widget.data_def:# == False:
        try:
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            if int(data_def["interval"]) * 60 < time.time() - info["last_update"]:
                result["widgetStatus"] = "noUpdate"
            data = list(current[2][0])
            ds = current[1]
            for i in range(0, len(ds)):
                if data_def.has_key(ds[i]):
                    field_def = data_def[ds[i]]
                    try:
                        data_rrd = rrdtool.fetch(rrd_path, "-s", str(int(last_update)-int(field_def[3]) * 60), "-e", last_update + "-1", "LAST")
                        data_rrd = map(lambda x:x[i],data_rrd[2])
                        result[ds[i]] = format_value_def(field_def,data_rrd)
                    except:
                        result[ds[i]] = format_value(field_def, data[i])
                    if result[ds[i]]["status"] == "error" and  result["widgetStatus"] != "noUpdate":
                        result["widgetStatus"] = "error"
                    elif result[ds[i]]["status"] == "warning" and result["widgetStatus"] != "error" and result["widgetStatus"] != "noUpdate":
                        result["widgetStatus"] = "warning"
                else:
                    result[ds[i]] = {"status":"unknown","value":str(data[i])}
        except:
            raise
            return widget.data_def
    else:
        result["widgetStatus"] = "unknown"
        for x,y in zip(current[1],current[2][0]):
            result[x] = {"status":"unknown","value":str(y)}

    return result

def getdata(projectId="all"):
    myResult = []
    servicesDict = {"ok":0,"warning":0,"error":0,"allProblem":0,"allType":0}
    widgetStatusProjects = {}
    if projectId == "all":
        projects = Project.objects.all().order_by("-sequence")
    else:
        projects = Project.objects.filter(id=projectId)
    for p in projects:
        widgetStatusProjects[p.id] = {'projectId':p.id,'projectName':p.name,'error':0,'warning':0,'ok':0,'unkown':0,"servicesValues":{}}
        for w in p.widget_set.all():
            try:
                result = paser_widget(w)
            except:
                continue
            if result['widgetStatus'] == "error" or result['widgetStatus'] == "noUpdate":
                servicesDict['error'] += 1
                widgetStatusProjects[p.id]['error'] += 1
            elif result['widgetStatus'] == "warning":
                servicesDict['warning'] += 1
                widgetStatusProjects[p.id]['warning'] += 1
            else:
                servicesDict['ok'] += 1
                widgetStatusProjects[p.id]['ok'] += 1
            widgetStatusProjects[p.id]['servicesValues'][w.id]=result
            cache.set("widgetData_"+str(w.id),result,settings.CACHE_TIME)
        myResult.append(widgetStatusProjects[p.id])
        cache.set("getdata_"+str(p.id),widgetStatusProjects,settings.CACHE_TIME)
    if projectId == "all":
        cache.set("getdata_all",myResult,settings.CACHE_TIME)
        cache.set("getdata_servicesDict",servicesDict,settings.CACHE_TIME)
    return myResult,servicesDict,widgetStatusProjects

def get_widget_diff_conf():
    widgetConfDifCount={"all":0,"same":0,"diff":0}
    widgetConfDifListId=[]
    widgets = Widget.objects.filter(dashboard__id=1).values("id","data_def","data_default")
    for w in widgets:
        if w['data_def'] == None or w['data_default'] != w['data_def']:
            widgetConfDifCount['diff'] += 1 
            widgetConfDifListId.append(w['id'])
        else:widgetConfDifCount['same'] += 1
    widgetConfDifCount['all'] = widgets.count()
    cache.set("widgetConfDifCount",widgetConfDifCount,settings.CACHE_TIME)
    cache.set("widgetConfDifListId",widgetConfDifListId,settings.CACHE_TIME)
    return widgetConfDifCount,widgetConfDifListId

@login_required()
@permission_required('user.is_staff')
def projects(request):
    myResult = cache.get("getdata_all")
    if myResult == None:
        myResult,servicesDict,widgetStatusProjects = getdata()
    dashboard_error = get_object_or_404(DashboardError, id=1)
    imgs = dashboard_error.graphs.all()
    startTime = int(time.mktime(datetime.strptime(time.strftime("%Y-%m-%d",time.localtime()),"%Y-%m-%d").timetuple()))
    endTime = startTime + 86400
    return render_to_response('html/overview_projects.html',
        {'projects':myResult,"imgs":imgs,"startTime":startTime,"endTime":endTime,"dashboard_error":dashboard_error,"imgsDivWidth":dashboard_error.width*2+5})

@login_required()
@permission_required('user.is_staff')
def showdetail_services(request,pid):
    widgetList = Widget.objects.filter(project__id=pid)
    categorys = widgetList.values("category__id","category__title").order_by("category__title").annotate()
    widgetStatusProjects = cache.get("getdata_"+str(pid))
    if widgetStatusProjects == None:
        myResult,servicesDict,widgetStatusProjects = getdata(pid)
    data = widgetStatusProjects[int(pid)]["servicesValues"]
    def get_data(widgets):
        result = [];
        for w in widgets:
            try:
                if data[w.id]['widgetStatus'] == "ok" or data[w.id]['widgetStatus']=="unknown":
                    raise
                dt = {"showTitle":"","category":w.category.title,"value":"<td>"+w.title+"</td>","widget":w}
                if data[w.id]['widgetStatus'] == "noUpdate":dt["value"] = "<td><div class='errornote'>No update</div>"+w.title+"</td>"
                for k in data[w.id]["valueList"]:
                    if data[w.id][k]["status"] == "warning":
                        dt["value"] += "<td><div class='errors'>"+data[w.id][k]["value"]+"</div></td>"
                    elif data[w.id][k]["status"] == "error":    
                        dt["value"] += "<td><div class='errornote'>"+data[w.id][k]["value"]+"</div></td>"
                    else:
                        dt["value"] += "<td>"+data[w.id][k]["value"]+"</td>"
                    dt["showTitle"] += "<th>"+k+"</th>"
                result.append(dt)
            except:
                pass
        return result
    result = []
    for c in categorys:
        widgetData = get_data(widgetList.filter(category__id=c["category__id"]))
        if widgetData != []:
            result.append(widgetData)
    return render_to_response('html/projects_sd_service.html',{"data":result})

@login_required()
def myhome(request):

    return render_to_response('html/main.html') 
    
def home_top(request):
    servicesDict = cache.get("getdata_servicesDict")
    if servicesDict == None:
        myResult,servicesDict,widgetStatusProjects = getdata()
    widgetConfDifCount = cache.get("widgetConfDifCount")
    if widgetConfDifCount == None:
        widgetConfDifCount,widgetConfDifListId = get_widget_diff_conf()
    
    return render_to_response('html/top.html',{"request":request,"services":servicesDict,"widgetStatus":widgetConfDifCount})
    
def home_center(request):

    return render_to_response('html/center.html',{"request":request})

def home_down(request):

    c = RequestContext(request,{})
    return render_to_response('html/down.html',c)

@login_required()
def home_left(request):

    c = RequestContext(request,{
        "request":request,
        "dashboards":request.user.dashboard_set.all().order_by("-sequence"),
        "error_dashboards":request.user.dashboarderror_set.all(),
        "projects":Project.objects.all().order_by("-sequence"),
        "services":ServiceType.objects.all(),
        "graph_aiders":GraphAider.objects.filter(user=request.user.id).all().order_by("-sequence"),
    })
    return render_to_response('html/left.html',c)

def project_servers(reqeust,pid):
    widgetStatusProjects = cache.get("getdata_"+str(pid))
    if widgetStatusProjects == None:
        myResult,servicesDict,widgetStatusProjects = getdata(pid)
    data = widgetStatusProjects[int(pid)]["servicesValues"]
    servers = Server.objects.filter(project__id=pid).order_by("ip")
    for s in servers:
        result = {"ok":0,"warning":0,"unknown":0,"error":0}
        widgets = Widget.objects.filter(server=s,project__id=pid).order_by("title")
        for w in widgets:
            try:
                if data[w.id]['widgetStatus'] == "ok":
                    result["ok"] += 1
                elif data[w.id]['widgetStatus']=="unknown":
                    result["unknown"] += 1
                elif data[w.id]['widgetStatus']=="warning":
                    result["warning"] += 1
                else:result["error"] += 1
            except:
                pass
        s.data=result
    if servers.count() > 16:
        t = servers.count()/2
        servers1 = servers[:t]
        servers2 = servers[t:]
    else:
        servers1 = servers
        servers2 = []
    return render_to_response('html/overview_project.html',{"pid":pid,"servers1":servers1,"servers2":servers2})

def project_server(request,pid,sid):
    '''
    widgetStatusProjects = cache.get("getdata_"+str(pid))
    if widgetStatusProjects == None:
        myResult,servicesDict,widgetStatusProjects = getdata(pid)
    data = widgetStatusProjects[int(pid)]["servicesValues"]
    for w in widgets:
        print w.id
        try:
            w.dt = {"showTitle":"","value":"<td>"+w.title+"</td>"}
            for k in data[w.id]["valueList"]:
                if data[w.id][k]["status"] == "warning":
                    w.dt["value"] += "<td><div class='errors'>"+data[w.id][k]["value"]+"</div></td>"
                elif data[w.id][k]["status"] == "error":    
                    w.dt["value"] += "<td><div class='errornote'>"+data[w.id][k]["value"]+"</div></td>"
                else:
                    w.dt["value"] += "<td>"+data[w.id][k]["value"]+"</td>"
                w.dt["showTitle"] += "<th>"+k+"</th>"
        except:
             pass
    '''
    widgets = Widget.objects.filter(project__id=pid,server__id=sid).order_by("title")
    return render_to_response('html/overview_project_server.html',{"widgets":widgets})

def problem_server(request):
    n = [];d = [];u = [];o = [];unknown = []
    servers = Server.objects.all().order_by("ip")
    for i in settings.EXCLUDE_IPS:
        servers = servers.exclude(ip__contains=i.replace("*",""))
    for s in servers:
        try:
            if s.power_on == "N":
                s.log = {"sign":"Off"}
                o.append(s)
            else:
                s.log = RemarkLog.objects.filter(mark=s.id,type=2).order_by("-id")[0]
                if s.log.sign == "Normal":n.append(s)
                elif s.log.sign == "Unstable":u.append(s)
                else:d.append(s)
        except:
            s.log = {"sign":"unknown"}
            unknown.append(s)
    return render_to_response('html/overview_problem_server.html',{"servers":d+u+unknown+n+o})

def problem_service(request):
    servers  = Server.objects.filter(power_on="Y")
    for i in settings.EXCLUDE_IPS:
        servers = servers.exclude(ip__contains=i.replace("*",""))
    def get_server_info(w):
        try:
            if w.server not in servers:w.serverInfo = {"sign":"Unknown"}
            else:w.serverInfo = RemarkLog.objects.filter(mark=w.server.id,type=2).order_by("-id")[0]
        except:pass
        return w
    result = []
    widgets = Widget.objects.filter(dashboard__id=1).order_by("category__title").annotate(categorys=Count("category"))
    for w in widgets:
        ls = []
        data =  cache.get("widgetData_"+str(w.id))
        if data == None:
            try:data = paser_widget(w)
            except:
                w.widgetStatus = "unknown"
                w.widgetData = "this widget config error, please check."
                result.append(w)
                w = get_server_info(w)
                continue
        if data["widgetStatus"] != "ok" and data["widgetStatus"] != "unknown":
            w.widgetStatus = data["widgetStatus"]
            for i in data["valueList"]:
                if data[i]["status"] != "ok" and data[i]["status"] != "unknown":
                    ls.append(i+":"+str(data[i]["value"]))
            w.widgetData = ",".join(ls)
            w = get_server_info(w)
            result.append(w)
    dashboard_error = get_object_or_404(DashboardError, id=1)
    imgs = dashboard_error.graphs.all()
    startTime = int(time.mktime(datetime.strptime(time.strftime("%Y-%m-%d",time.localtime()),"%Y-%m-%d").timetuple()))
    endTime = startTime + 86400
    alarmlogs = AlarmLog.objects.filter(created_on__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-created_on")
    frequentAlarmLogs = FrequentAlarmLog.objects.filter(lasterror_time__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-lasterror_time")
    return render_to_response('html/overview_problem_service.html',{"dashboard_error":dashboard_error,"imgs":imgs,"startTime":startTime,"endTime":endTime,"service":result,"alarmlogs":alarmlogs,"frequentAlarmLogs":frequentAlarmLogs})

def widget_diff_conf(request):
    widgetConfDifListId = cache.get("widgetConfDifListId")
    if widgetConfDifListId == None:
        widgetConfDifCount,widgetConfDifListId = get_widget_diff_conf()
    widgets = Widget.objects.filter(id__in=widgetConfDifListId).values("id","title","data_def","data_default")
    return render_to_response('html/show_widget_diff_conf.html',{"widgets":widgets})
