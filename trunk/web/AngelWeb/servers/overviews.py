from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import cache_page
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
    myResult = [];widgetStatusProjects = {}
    servicesDict = {"ok":0,"warning":0,"error":0,"allProblem":0,"allType":0}
    serverStatus = cache.get("serverStatus")
    if serverStatus == None:
        serverStatus = {}
        t = time.strftime("%Y-%m-%d %H:%M:00",time.localtime(time.time()-60))
        remarkLogs = ServerPing.objects.filter(created_time=t).values("mark","sign")
        for x in remarkLogs:
            serverStatus[x["mark"]] = x["sign"]
    if projectId == "all":
        projects = Project.objects.all().order_by("-sequence")
    else:
        projects = Project.objects.filter(id=projectId)
    for p in projects:
        widgetStatusProjects[p.id] = {'projectId':p.id,'projectName':p.name,'error':0,'warning':0,'ok':0,'unkown':0,"servicesValues":{},"serversDict":{}}
        for w in p.widget_set.filter(dashboard__id=1):
            try:
                result = paser_widget(w)
            except:
                continue
            if result['widgetStatus'] == "error" or result['widgetStatus'] == "noUpdate":
                widgetStatusProjects[p.id]['error'] += 1
                servicesDict['error'] += 1
            elif result['widgetStatus'] == "warning":
                widgetStatusProjects[p.id]['warning'] += 1
                servicesDict['warning'] += 1
            else:
                widgetStatusProjects[p.id]['ok'] += 1
                servicesDict['ok'] += 1
            widgetStatusProjects[p.id]['servicesValues'][w.id]=result
            cache.set("widgetData_"+str(w.id),result,settings.CACHE_TIME)
        
        servers = Server.objects.filter(project=p,power_on="Y").values_list("id",flat=True)
        serverDict = {"ok":0,"warning":0,"error":0,"allProblem":0,"allType":0}
        for i in servers:
            try:
                if serverStatus[i] == "Normal":serverDict["ok"] += 1 
                elif serverStatus[i] == "Unstable":serverDict["warning"] += 1
                else:serverDict["error"] += 1
            except:
                pass
        widgetStatusProjects[p.id]["serversDict"] = serverDict
        myResult.append(widgetStatusProjects[p.id])
        cache.set("getdata_"+str(p.id),widgetStatusProjects,settings.CACHE_TIME)
        
    if projectId == "all":
        cache.set("getdata_all",myResult,settings.CACHE_TIME)
        servicesDict["allProblem"] = servicesDict["warning"] + servicesDict["error"]
        servicesDict["allType"] = servicesDict["allProblem"] + servicesDict["ok"]
        cache.set("getdata_servicesDict",servicesDict,settings.CACHE_TIME)
    return myResult,servicesDict,widgetStatusProjects

def get_server_data():
    t = time.strftime("%Y%m%d%H%M",time.localtime(time.time()-60))
    myTime = time.strftime("%Y-%m-%d %H:%M:00",time.localtime(time.time()-60))
    data = ServerPing.objects.filter(created_time=myTime).values("sign").annotate(count=Count("sign"))
    serverDict = cache.get("serverDict_"+t)
    if serverDict != None:
        cache.set("get_server_data_serverDict",serverDict,settings.CACHE_TIME)
        return serverDict
    serverDict = {"ok":0,"warning":0,"error":0,"allProblem":0,"allType":0}
    for d in data:
        if d["sign"] == "Normal":serverDict["ok"] = d["count"]
        elif d["sign"] == "Unstable":serverDict["warning"] = d["count"]
        else:serverDict["error"] = d["count"]
    serverDict["allProblem"] = serverDict["warning"] + serverDict["error"]
    serverDict["allType"] = serverDict["allProblem"] + serverDict["ok"]
    cache.set("get_server_data_serverDict",serverDict,settings.CACHE_TIME)
    return serverDict

def get_ticket_data():
    ticketDict = {"new":0,"processing":0,"closed":0,"done":0}
    ticket = Ticket.objects.all().values("status").annotate(count=Count("status"))
    for t in ticket:
        if t["status"] == "New":ticketDict["new"] = t["count"]
        elif t["status"] == "Processing":ticketDict["processing"] = t["count"]
        elif t["status"] == "Closed":ticketDict["closed"] = t["count"]
        else:ticketDict["done"] = t["count"]
    cache.set("get_ticket_data_ticketDict",ticketDict,settings.CACHE_TIME)
    return ticketDict

def get_widget_diff_conf():
    widgetConfDifCount={"all":0,"same":0,"diff":0}
    widgetConfDifListId=[]
    ignoreCount = RemarkLog.objects.filter(type=4).count()
    widgets = Widget.objects.filter(dashboard__id=1).values("id","data_def","data_default")
    for w in widgets:
        if w['data_def'] == None or w['data_default'] != w['data_def']:
            widgetConfDifListId.append(w['id'])
            widgetConfDifCount['diff'] += 1 
        elif Alarm.objects.filter(widget__id=w["id"]).count() < 1:
            widgetConfDifCount['diff'] += 1 
            widgetConfDifListId.append(w['id'])
        else:widgetConfDifCount['same'] += 1
    widgetConfDifCount['all'] = widgets.count()
    widgetConfDifCount['diff'] = widgetConfDifCount['diff'] - ignoreCount
    cache.set("widgetConfDifCount",widgetConfDifCount,settings.CACHE_TIME)
    cache.set("widgetConfDifListId",widgetConfDifListId,settings.CACHE_TIME)
    return widgetConfDifCount,widgetConfDifListId

@login_required()
def projects(request):
    if not request.user.is_staff:
        raise Http404
    myResult = cache.get("getdata_all")
    if myResult == None:
        myResult,servicesDict,widgetStatusProjects = getdata()
    dashboard_error = get_object_or_404(Dashboard, title="Overall")
    imgs = dashboard_error.graphs.all()
    startTime = int(time.mktime(datetime.strptime(time.strftime("%Y-%m-%d",time.localtime()),"%Y-%m-%d").timetuple()))
    endTime = startTime + 86400
    return render_to_response('html/overview_projects.html',
        {'projects':myResult,"imgs":imgs,"startTime":startTime,"endTime":endTime,"dashboard_error":dashboard_error,"imgsDivWidth":dashboard_error.width*2+5})

@login_required()
def showdetail_services(request,pid):
    if not request.user.is_staff:
        raise Http404
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
    url = None
    if "url" in request.GET:
        url = request.GET["url"]
    return render_to_response('html/main.html',{"url":url}) 
    
def home_top(request):
    if request.GET.has_key("action"):
        serverDict = get_server_data()
        myResult,servicesDict,widgetStatusProjects = getdata()
        ticketDict = get_ticket_data()
        widgetConfDifCount,widgetConfDifListId = get_widget_diff_conf()
    else:
        serverDict = cache.get("get_server_data_serverDict")
        if serverDict == None:
            serverDict = get_server_data()
        servicesDict = cache.get("getdata_servicesDict")
        if servicesDict == None:
            myResult,servicesDict,widgetStatusProjects = getdata()
        ticketDict = cache.get("get_ticket_data_ticketDict")
        if ticketDict == None:
            ticketDict = get_ticket_data()
        widgetConfDifCount = cache.get("widgetConfDifCount")
        if widgetConfDifCount == None:
            widgetConfDifCount,widgetConfDifListId = get_widget_diff_conf()
    st = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()-180))
    ed = time.strftime("%Y-%m-%d %H:%M:%S")
    serverUpdate = ServerPing.objects.filter(created_time__gte=st,created_time__lte=ed).count()
    try:
        log = ExtraLog.objects.filter(type=6)[0]
        call = log.value
    except:
        log = ExtraLog(type=6)
        call = "off"
    if request.GET.has_key("call") and request.user.is_authenticated():
        c = request.GET.get("call","")
        if c == "on":
            log.value = "on"
            log.save()
            call == "on"
        elif c == "off":
            log.value = "off"
            log.save()
            call == "off"
        l = DisableAlarmLog()
        l.name = request.user.username
        l.action = c
        l.save()
        return HttpResponseRedirect("/home/top")
    disAlarmPros = Project.objects.filter(alarm="False").count()
    disAlarms = Alarm.objects.filter(enable="False").count()
    return render_to_response('html/top.html',{"request":request,"call":call,"disAlarmPros":disAlarmPros,"disAlarms":disAlarms,"serverUpdate":serverUpdate,"tickets":ticketDict,"servers":serverDict,"services":servicesDict,"widgetStatus":widgetConfDifCount})
    
def home_center(request):
    url = None
    if "url" in request.GET:
        url = request.GET["url"]
    return render_to_response('html/center.html',{"request":request,"url":url})

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
        "services":WidgetServiceType.objects.all(),
        "graph_aiders":GraphAider.objects.filter(user=request.user.id).all().order_by("-sequence"),
    })
    return render_to_response('html/left.html',c)

def project_servers(reqeust,pid):
    widgetStatusProjects = cache.get("getdata_"+str(pid))
    if widgetStatusProjects == None:
        myResult,servicesDict,widgetStatusProjects = getdata(pid)
    data = widgetStatusProjects[int(pid)]["servicesValues"]
    servers = Server.objects.filter(project__id=pid).exclude(server_function=4).order_by("ip")
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
    n = [];d = [];u = [];o = [];unknown = [];tDt = {}
    myTime = time.strftime("%Y-%m-%d %H:%M:00",time.localtime(time.time()-60))
    logs = ServerPing.objects.filter(created_time=myTime)
    for i in logs:tDt[i.mark] = i
    servers = Server.objects.all().order_by("ip")
    for i in settings.EXCLUDE_IPS:
        servers = servers.exclude(ip__contains=i.replace("*",""))
    for s in servers:
        try:
            if s.power_on == "N":
                s.log = {"sign":"Off"}
                o.append(s)
            else:
                s.log = tDt[s.id]
                if s.log.sign == "Normal":n.append(s)
                elif s.log.sign == "Unstable":u.append(s)
                else:d.append(s)
        except:
            s.log = {"sign":"unknown"}
            unknown.append(s)
    return render_to_response('html/overview_problem_server.html',{"servers":d+u+unknown+n+o})

@login_required
@cache_page(settings.CACHE_TIME)
def problem_service(request,did):
    if not request.user.is_staff:
        raise Http404
    t = time.strftime("%Y-%m-%d %H:%M:00",time.localtime(time.time()-60))
    servers  = Server.objects.filter(power_on="Y").values_list("id",flat=True)
    for i in settings.EXCLUDE_IPS:
        servers = servers.exclude(ip__contains=i.replace("*",""))
    def get_server_info(w):
        try:
            if w.server.id not in servers:w.serverInfo = {"sign":"Unknown"}
            else:w.serverInfo = ServerPing.objects.filter(mark=w.server.id,created_time=t)[0]
        except:pass
        return w
    result = []
    widgets = Widget.objects.filter(dashboard__id=did).order_by("category__title").annotate(categorys=Count("category"))
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
    dashboard = get_object_or_404(Dashboard, id=did)
    startTime = int(time.mktime(datetime.strptime(time.strftime("%Y-%m-%d",time.localtime()),"%Y-%m-%d").timetuple()))
    endTime = startTime + 86400
    alarmlogs = AlarmLog.objects.filter(created_on__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-created_on")
    frequentAlarmLogs = FrequentAlarmLog.objects.filter(lasterror_time__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-lasterror_time")
    return render_to_response('html/overview_problem_service.html',{"dashboard":dashboard,"startTime":startTime,"endTime":endTime,"service":result,"alarmlogs":alarmlogs,"frequentAlarmLogs":frequentAlarmLogs})

def widget_diff_conf(request):
    if request.GET.has_key("wid"):
        wid = request.GET["wid"]
        action = request.GET["action"]
        if action == "Resume":
            RemarkLog.objects.filter(type=4,mark=wid).delete()
        elif action == "Ignore":
            RemarkLog(type=4,mark=wid).save()
        return HttpResponseRedirect("/overview/widget/diff_conf/")
    widgetConfDifListId = cache.get("widgetConfDifListId")
    if widgetConfDifListId == None:
        widgetConfDifCount,widgetConfDifListId = get_widget_diff_conf()
    widgets = Widget.objects.filter(id__in=widgetConfDifListId).values("id","title","data_def","data_default")
    ignoreWidgets = list(RemarkLog.objects.filter(type=4).values_list("mark",flat=True).annotate())
    for w in widgets:
        if w["data_def"] == w["data_default"]:w["alarm"] = "Not"
        else:w["alarm"] = "Unknown"
        if w["id"] in ignoreWidgets:
            w["ignore"] = True
            ignoreWidgets.remove(w["id"])
        else:w["ignore"] = False
    RemarkLog.objects.filter(type=4,mark__in=ignoreWidgets).delete()
    widgets = sorted(widgets, key=lambda x:x["ignore"])
    return render_to_response('html/show_widget_diff_conf.html',{"widgets":widgets})

@login_required()
def quick_view(request):
    import re
    import json
    data = cache.get("quick_view_widgets")
    if data == None:
        result = {}
        widgets = Widget.objects.exclude(project=None).filter(dashboard__id=1)
        projects = Project.objects.filter(widget__in=widgets).annotate().order_by("-sequence").values("id","name")
        for p in projects:
            result[p["name"]] = {}
            categorys = WidgetCategory.objects.filter(widget__in=widgets.filter(project__id=p["id"])).values("id","title").annotate()
            for c in categorys:
                cc = {}
                try:
                    widget = widgets.filter(project__id=p["id"],category__id=c["id"])[0]
                    data = re.findall(r"DS:(\S+):G",widget.rrd.setting)
                    for i in data:
                        cc[i] = i
                    result[p["name"]][c["title"]]=cc
                except:pass
        data = json.dumps(result,ensure_ascii=False)
        cache.set("quick_view_widgets",data,300)
    e = int(time.time())
    p = request.GET.get("v_",None)
    c = request.GET.get("v__",None)
    v = request.GET.get("v",None)
    t = request.GET.get("t",None)
    if t == "Last Hour":s = e - 3600
    elif t == "Last 7 Hour":s = e - 3600 * 7
    else:
        sT = time.strptime(time.strftime("%Y%m%d",time.localtime()),"%Y%m%d")
        s = int(time.mktime(sT))
        e = s + 86400
    
    return render_to_response("html/quick_view.html",{"data":data,"p":p,"c":c,"v":v,"s":s,"e":e,"w":1000,"h":500})

def quick_view_img(request):
    from subprocess import Popen, PIPE
    color = ["#EA0000","#000000","#2828FF","#28FF28","#F9F900","#00FFFF","#9999CC","#D9B3B3","#E2C2DE","#CA8EFF","#EA0000","#000000","#2828FF","#28FF28","#F9F900","#00FFFF","#9999CC","#D9B3B3","#E2C2DE","#CA8EFF"]
    p = request.GET["p"]
    c = request.GET["c"]
    v = request.GET["v"]
    w = request.GET["w"]
    h = request.GET["h"]
    s = request.GET["s"]
    e = request.GET["e"]
    line = ""
    widgets = Widget.objects.filter(dashboard__id=1,project__name=p,category__title=c).order_by("title")
    for n in range(len(widgets)):
        line += 'DEF:%s=%s:%s:LAST LINE:%s%s:"%s" ' % (n,widgets[n].rrd.path(),v,n,color[n],widgets[n].title)
    cmd = 'rrdtool graph - -E --imgformat PNG -s %s -e %s -t "%s" --width %s --height %s %s' % (s, e, p+" - "+c+" - "+v, w, h, line)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    
    if len(stderr) > 0:
        response = HttpResponse(stderr)
        response["content-type"] = "text/plain"
        return response
    response = HttpResponse(stdout)
    response["content-type"] = "image/png"
    return response

def get_show_key(data):
    titleKey = []
    for i in data.replace(";",",").split(","):
        try:
            titleKey.append(i.split(":"))
        except:continue
    return titleKey

def api_show_widget_detail(request,wid):
    import json
    ls = [];lines = []
    w = get_object_or_404(Widget,id=wid)
    widgetStatus = paser_widget(w)
    ls.append(["title",w.title])
    ls.append(["widget status",widgetStatus["widgetStatus"]])
    try:
        d = w.detectorinfo_set.all().order_by("-id")[0]
        detectorInfo = json.loads(d.data)
    except:detectorInfo = {}
    if w.service_type and w.service_type.show_detail_key:
        for title,titleKey in get_show_key(w.service_type.show_detail_key):
            if titleKey in widgetStatus["valueList"]:lines.append(titleKey)
            if titleKey in widgetStatus:ls.append([title,widgetStatus[titleKey]["value"]])
            elif titleKey in detectorInfo:ls.append([title,detectorInfo[titleKey]])
            else:ls.append([title,""])
    ls.append(["production",",".join(w.dashboard.values_list("title",flat=True))])
    start = int(time.time() - time.time() % 86400)
    return render_to_response("cmdb/show_widget_detail.html",{"result":ls,"widget":w,"start":start,"end":start+86400,"lines":lines})

def update_widget_info(request):
    wid = request.GET["wid"]
    remark = request.GET["remark"]
    widget = get_object_or_404(Widget,id=wid)
    widget.remark = remark
    widget.save()
    return HttpResponse("ok")

@login_required()
def availability(request):
    try:
       s = request.GET["s"]
       e = request.GET["e"]
       time.strptime(s, "%Y-%m-%d")
       time.strptime(e, "%Y-%m-%d")
    except:
       s = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))
       e = time.strftime("%Y-%m-%d")
    projects = Project.objects.all()
    allServerSatus = {"Down":0,"Unstable":0,"Normal":0}
    logs = ServerPing.objects.filter(created_time__gte=s+" 00:00:00",created_time__lte=e+" 23:59:59").values("mark","sign")
    data = logs.annotate(Count=Count('sign')).order_by('mark')
    for p in projects:
        p.serverIds = list(Server.objects.filter(power_on="Y",project=p).values_list("id",flat=True))
        p.serverData = {"Down":0,"Unstable":0,"Normal":0}
        for d in data:
            if d["mark"] in p.serverIds:
                p.serverData[d["sign"]] += d["Count"]
        alls = float(sum(p.serverData.values()))
        if p.serverData["Down"] == 0:p.serverData["Down_p"] = 0
        else:p.serverData["Down_p"] = "%0.2f" % (p.serverData["Down"] * 100 / alls)
        if p.serverData["Unstable"] == 0:p.serverData["Unstable_p"] = 0
        else:p.serverData["Unstable_p"] = "%0.2f" % (p.serverData["Unstable"] * 100 / alls)
        if p.serverData["Normal"] == 0:p.serverData["Normal_p"] = 0
        else:p.serverData["Normal_p"] = "%0.2f" % (p.serverData["Normal"] * 100 / alls)
    for d in data:
        allServerSatus[d["sign"]] += d["Count"]
    normalLs = [];downLs = [];unstableLs = [];dateLs = [];minLs = []
    for i in range(int(time.mktime(time.strptime(s, "%Y-%m-%d"))),int(time.mktime(time.strptime(e, "%Y-%m-%d"))),86400):
        si = time.strftime("%Y-%m-%d",time.localtime(i))
        ei = time.strftime("%Y-%m-%d",time.localtime(i+86400))
        n = 0;d = 0;u = 0
        for i in ServerPing.objects.filter(created_time__gte=si+" 00:00:00",created_time__lte=ei+" 23:59:59").values("sign").annotate(Count=Count('sign')):
            if i["sign"] == "Normal":n = i["Count"]
            elif i["sign"] == "Down":d = i["Count"]
            elif i["sign"] == "Unstable":u = i["Count"]
        normalLs.append(n)
        downLs.append(d)
        unstableLs.append(u)
        dateLs.append(si)
        try:perD = d * 100 / (n + d +u)
        except:perD = 0
        try:perU = u * 100 / (n + d +u)
        except:perU = 0
        if perD != 100 and perD != 0:minLs.append(perD)
        if perU != 100 and perU != 0:minLs.append(perU)
    interval = 0
    if len(dateLs) > 10:interval = len(dateLs) / 8
    if interval == 1:interval = 2
    try:minValue = 99 - max(minLs)
    except:minValue = 99
    return render_to_response("html/report_availability.html",locals())

@login_required()
def availability_project_detail(request,pid):
    try:
       st = request.GET["s"]
       ed = request.GET["e"]
       time.strptime(st, "%Y-%m-%d")
       time.strptime(ed, "%Y-%m-%d")
    except:
       st = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))
       ed = time.strftime("%Y-%m-%d")
    allServerSatus = {"Down":0,"Unstable":0,"Normal":0};dt = {};serverDt = {}
    project = Project.objects.get(id=pid)
    servers = Server.objects.filter(project=pid)
    for s in servers:
        serverDt[s.id] = s.ip
    logs = ServerPing.objects.filter(mark__in=serverDt.keys(),created_time__gte=st+" 00:00:00",created_time__lte=ed+" 23:59:59").values("mark","sign").annotate(Count=Count('sign')).order_by('mark')
    for l in logs:
        if l["mark"] not in dt:dt[l["mark"]] = {"Down":0,"Unstable":0,"Normal":0}
        dt[l["mark"]][l["sign"]]=l["Count"]
        dt[l["mark"]]["mark"] = l["mark"]
        allServerSatus[l["sign"]] += l["Count"]
    ls = dt.values()
    for d in ls:
        alls = float(sum(d.values())-d["mark"])
        d["ip"] = serverDt[d["mark"]]
        if d["Down"] == 0:d["Down_p"] = 0
        else:d["Down_p"] = float("%0.2f" % (d["Down"] * 100 / alls))
        if d["Unstable"] == 0:d["Unstable_p"] = 0
        else:d["Unstable_p"] = float("%0.2f" % (d["Unstable"] * 100 / alls))
        if d["Normal"] == 0:d["Normal_p"] = 0
        else:d["Normal_p"] = "%0.2f" % (d["Normal"] * 100 / alls)
    ls = sorted(ls,key=lambda l:l["Unstable_p"],reverse = True)
    ls = sorted(ls,key=lambda l:l["Down_p"],reverse = True)
    allServerSatusCount = sum(allServerSatus.values())
    if allServerSatus["Down"] == 0:allServerSatus["Down_p"] = 0
    else:allServerSatus["Down_p"] = "%0.2f" % (allServerSatus["Down"] * 100.0 /allServerSatusCount)
    if allServerSatus["Normal"] == 0:allServerSatus["Normal_p"] = 0
    else:allServerSatus["Normal_p"] = "%0.2f" % (allServerSatus["Normal"] * 100.0 /allServerSatusCount)
    if allServerSatus["Unstable"] == 0:allServerSatus["Unstable_p"] = 0
    else:allServerSatus["Unstable_p"] = "%0.2f" % (allServerSatus["Unstable"] * 100.0 /allServerSatusCount)
    
    normalLs = [];downLs = [];unstableLs = [];dateLs = [];minLs = []
    for i in range(int(time.mktime(time.strptime(st, "%Y-%m-%d"))),int(time.mktime(time.strptime(ed, "%Y-%m-%d"))),86400):
        si = time.strftime("%Y-%m-%d",time.localtime(i))
        ei = time.strftime("%Y-%m-%d",time.localtime(i+86400))
        n = 0;d = 0;u = 0
        for i in ServerPing.objects.filter(mark__in=serverDt.keys(),created_time__gte=si+" 00:00:00",created_time__lte=ei+" 23:59:59").values("sign").annotate(Count=Count('sign')):
            if i["sign"] == "Normal":n = i["Count"]
            elif i["sign"] == "Down":d = i["Count"]
            elif i["sign"] == "Unstable":u = i["Count"]
        normalLs.append(n)
        downLs.append(d)
        unstableLs.append(u)
        dateLs.append(si)
        perD = d * 100 / (n + d +u)
        perU = u * 100 / (n + d +u)
        if perD != 100 and perD != 0:minLs.append(perD)
        if perU != 100 and perU != 0:minLs.append(perU)
    interval = 0
    if len(dateLs) > 10:interval = len(dateLs) / 8
    if interval == 1:interval = 2
    try:minValue = 99 - max(minLs)
    except:minValue = 99
    
    return render_to_response("html/report_availability_project_detail.html",locals())


@login_required()
def availability_server(request):
    try:
        st = request.GET["st"]
        ed = request.GET["ed"]
        time.strptime(st,"%Y-%m-%d")
        time.strptime(ed,"%Y-%m-%d")
    except:
        st = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))
        ed = time.strftime("%Y-%m-%d")
    serverDt = {};dt = {}
    servers = Server.objects.all().order_by("ip")
    for s in servers:
        serverDt[s.id] = s.ip
    logs = ServerPing.objects.filter(created_time__gte=st+" 00:00:00",created_time__lte=ed+" 23:59:59").values("mark","sign").annotate(Count=Count('sign'))
    for l in logs:
        if l["mark"] not in serverDt:continue
        if l["mark"] not in dt:dt[l["mark"]] = {"Down":0,"Unstable":0,"Normal":0}
        dt[l["mark"]][l["sign"]]=l["Count"]
        dt[l["mark"]]["mark"] = l["mark"]
    ls = dt.values()
    for d in ls:
        alls = float(sum(d.values())-d["mark"])
        d["ip"] = serverDt[d["mark"]]
        if d["Down"] == 0:d["Down_p"] = 0
        else:d["Down_p"] = float("%0.2f" % (d["Down"] * 100 / alls))
        if d["Unstable"] == 0:d["Unstable_p"] = 0
        else:d["Unstable_p"] = float("%0.2f" % (d["Unstable"] * 100 / alls))
        if d["Normal"] == 0:d["Normal_p"] = 0
        else:d["Normal_p"] = "%0.2f" % (d["Normal"] * 100 / alls)
    ls = sorted(ls,key=lambda l:l["Unstable_p"],reverse = True)
    ls = sorted(ls,key=lambda l:l["Down_p"],reverse = True)
    return render_to_response("html/report_server.html",locals())

@login_required()
def availability_server_detail(request,sid):
    try:
       s = request.GET["s"]
       e = request.GET["e"]
       time.strptime(s, "%Y-%m-%d")
       time.strptime(e, "%Y-%m-%d")
    except:
       s = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))
       e = time.strftime("%Y-%m-%d")
    allServerSatus = {"Down":0,"Unstable":0,"Normal":0};pingLoss = []; pingTime = []; pingMin = []; pingMax= []; pingAvg = [];pingCreatedOn = []
    server = get_object_or_404(Server,id=sid)
    logs = ServerPing.objects.filter(mark=sid,created_time__gte=s+" 00:00:00",created_time__lte=e+" 23:59:59").values("mark","sign").annotate(Count=Count('sign'))
    for l in logs:
        allServerSatus[l["sign"]] = l["Count"]
    
    avgData = {}
    data = ServerPing.objects.filter(mark=sid,created_time__gte=s+" 00:00:00",created_time__lte=e+" 23:59:59")#.values("mark","sign").annotate(Count=Count('sign'))
    for d in data:
        key = str(d.created_time)[:13]
        try:
            v = eval(d.value)
        except:continue
        if key in avgData:
            avgData[key]["time"].append(float(v["time"]))
            avgData[key]["loss"].append(float(v["loss"]))
            avgData[key]["max"].append(float(v["max"]))
            avgData[key]["min"].append(float(v["min"]))
            avgData[key]["avg"].append(float(v["avg"]))
        else:
            avgData[key]={"time":[float(v["time"])],"loss":[float(v["loss"])],"max":[float(v["max"])],"min":[float(v["min"])],"avg":[float(v["avg"])]}
        '''
        try:
            v = eval(d.value)
            pingLoss.append(float(v["loss"]))
            pingTime.append(float(v["time"]))
            pingMax.append(float(v["max"]))
            pingMin.append(float(v["min"]))
            pingAvg.append(float(v["avg"]))
        except:
            pingLoss.append(100)
            pingTime.append(-1)
            pingMax.append(-1)
            pingMin.append(-1)
            pingAvg.append(-1)
        ''' 
        #pingCreatedOn.append(str(d.created_time))
    keys = avgData.keys()
    keys = sorted(keys)
    for i in keys:
        d = avgData[i]
        pingCreatedOn.append(i+":00:00")
        pingLoss.append(float("%0.2f" % (sum(d["loss"])/len(d["loss"]))))
        pingTime.append(float("%0.2f" % (sum(d["time"])/len(d["time"]))))
        pingMax.append(float("%0.2f" % (sum(d["max"])/len(d["max"]))))
        pingMin.append(float("%0.2f" % (sum(d["min"])/len(d["min"]))))
        pingAvg.append(float("%0.2f" % (sum(d["avg"])/len(d["avg"]))))
    interval = 0
    if len(pingCreatedOn) > 11:
        interval = len(pingCreatedOn) / 10
    
    normalLs = [];downLs = [];unstableLs = [];dateLs = [];minLs = []
    for i in range(int(time.mktime(time.strptime(s, "%Y-%m-%d"))),int(time.mktime(time.strptime(e, "%Y-%m-%d"))),86400):
        si = time.strftime("%Y-%m-%d",time.localtime(i))
        ei = time.strftime("%Y-%m-%d",time.localtime(i+86400))
        n = 0;d = 0;u = 0
        for i in ServerPing.objects.filter(mark=sid,created_time__gte=si+" 00:00:00",created_time__lte=ei+" 23:59:59").values("sign").annotate(Count=Count('sign')):
            if i["sign"] == "Normal":n = i["Count"]
            elif i["sign"] == "Down":d = i["Count"]
            elif i["sign"] == "Unstable":u = i["Count"]
        normalLs.append(n)
        downLs.append(d)
        unstableLs.append(u)
        dateLs.append(si)
        perD = d * 100 / (n + d +u)
        perU = u * 100 / (n + d +u)
        if perD != 100 and perD != 0:minLs.append(perD)
        if perU != 100 and perU != 0:minLs.append(perU)
    intervalArea = 0
    if len(dateLs) > 10:intervalArea = len(dateLs) / 10
    try:minValue = 99 - max(minLs)
    except:minValue = 99
    return render_to_response("html/report_server_detail.html",locals())

def overviews_services(request):
    widgets = Widget.objects.filter(dashboard=1)
    wsts = WidgetServiceType.objects.all()
    if len(widgets) > 0 and cache.get("widgetData_"+str(widgets[0].id)) == None:
        myResult,servicesDict,widgetStatusProjects = getdata()
    for wst in wsts:
        dt = {"ok":0,"warning":0,"unknown":0,"noUpdate":0,"error":0}
        for w in widgets.filter(service_type=wst.id):
            try:
                data = cache.get("widgetData_"+str(w.id))
                dt[data["widgetStatus"]] += 1
            except:pass
        wst.widgetStatus = dt
    interval = len(wsts) / 2
    wsts1 = wsts[:interval]
    wsts2 = wsts[interval:]
    return render_to_response("html/overview_services.html",{"wsts1":wsts1,"wsts2":wsts2}) 

def services_detail(request,wstid):
    widgets = Widget.objects.filter(service_type=wstid,dashboard=1)
    return render_to_response("html/show_widget_as_dashboard.html",{"widgets":widgets})
    
    
def services_type(request,sid):
    t = time.strftime("%Y-%m-%d %H:%M:00",time.localtime(time.time()-60))
    widgets = Widget.objects.filter(service_type=sid,dashboard=1)
    if len(widgets) > 0 and cache.get("widgetData_"+str(widgets[0].id)) == None:
        myResult,servicesDict,widgetStatusProjects = getdata()
    for w in widgets:
        w.serviceStatus = cache.get("widgetData_"+str(w.id))
        if w.server:
            try:w.serverStatus = ServerPing.objects.get(mark=w.server.id,created_time=t)
            except:pass
    if len(widgets) > 20:
        interval = len(widgets) / 2
        widgets1 = widgets[:interval]
        widgets2 = widgets[interval:]
    else:widgets1 = widgets
    return render_to_response("html/overview_service_detail.html",locals())

def services_type_widget(request,wid):
    widgets = Widget.objects.filter(id=wid)
    return render_to_response("html/show_widget_as_dashboard.html",{"widgets":widgets})

def paser_widget_error_time(widget,start,end):
    result = {"error":0,"warning":0,"ok":0,"all":0}
    if widget.data_def:
        try:
            current = rrdtool.fetch(widget.rrd.path(), "-s", str(start) + "-1", "-e", str(end), "LAST")
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            ds = current[1]
            for i in range(0, len(ds)):
                if data_def.has_key(ds[i]):
                    field_def = data_def[ds[i]]
                    try:
                        for x in current[2]:
                            if x[i] == None:continue
                            elif eval(str(x[i])+field_def[2]):result["error"] += 1
                            elif eval(str(x[i])+field_def[1]):result["warning"] += 1
                            else:result["ok"] += 1
                    except:
                        raise
        except:
            pass
    result["all"] = result["error"] + result["warning"] + result["ok"]
    return result

@login_required()
def availability_service(requst):
    try:
        s = requst.GET["s"]
        e = requst.GET["e"]
    except:
        s = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))
        e = time.strftime("%Y-%m-%d")
    error = [];warning = [];ok = [];ip = [];allData = []
    start = time.mktime(time.strptime(s,"%Y-%m-%d"))
    end = time.mktime(time.strptime(e,"%Y-%m-%d"))
    projects = Project.objects.all().order_by("name")
    services = WidgetServiceType.objects.all().order_by("name")
    try:
        project = int(requst.GET["p"])
        service = int(requst.GET["st"])
        widgets = Widget.objects.filter(project = project,service_type = service).order_by("server__ip")
        for w in widgets:
            data = paser_widget_error_time(w,int(start),int(end))
            error.append(data["error"])
            warning.append(data["warning"])
            ok.append(data["ok"])
            if w.server:ip.append(str(w.server.ip))
            else:ip.append("")
            if data["error"] == 0:data["error_p"] = 0
            else:data["error_p"] = data["error"] * 100 / data["all"]
            if data["warning"] == 0:data["warning_p"] = 0
            else:data["warning_p"] = data["warning"] * 100 / data["all"]
            if data["ok"] == 0:data["ok_p"] = 0
            else:data["ok_p"] = data["ok"] * 100 / data["all"]
            w.serviceStatus = data
    except:
        pass
    return render_to_response("html/report_availability_service.html",locals())


def get_rrd_line_value(rrd,start,end,line):
    import rrdtool
    current = rrdtool.fetch(rrd, "-s", str(start) + "-1", "-e", str(end), "LAST")
    for i in range(0,len(current[1])):
        if current[1][i] == line:
            break
    return map(lambda x:x[i],current[2])
    
    
@login_required()
def availability_trends_perf(request):
    import re
    import json
    data = cache.get("quick_view_widgets")
    if data == None:
        result = {}
        widgets = Widget.objects.exclude(project=None).filter(dashboard__id=1)
        projects = Project.objects.filter(widget__in=widgets).annotate().order_by("-sequence").values("id","name")
        for p in projects:
            result[p["name"]] = {}
            categorys = WidgetCategory.objects.filter(widget__in=widgets.filter(project__id=p["id"])).values("id","title").annotate()
            for c in categorys:
                cc = {}
                try:
                    widget = widgets.filter(project__id=p["id"],category__id=c["id"])[0]
                    data = re.findall(r"DS:(\S+):G",widget.rrd.setting)
                    for i in data:
                        cc[i] = i
                    result[p["name"]][c["title"]]=cc
                except:pass
        data = json.dumps(result,ensure_ascii=False)
        cache.set("quick_view_widgets",data,300)
    widgets = []
    p = request.GET.get("v_",None)
    c = request.GET.get("v__",None)
    v = request.GET.get("v",None)
    now = int(time.time())
    tmp = now % 86400
    end = now - tmp + 86400
    start = end - 86400 * 6
    startTime = time.strftime("%Y-%m-%d",time.localtime(start))
    endTime = time.strftime("%Y-%m-%d",time.localtime(end))
    if v != None:
        widgets = Widget.objects.filter(project__name=p,category__title=c)
        for w in widgets:
            w.line=[]
            dataTemp = get_rrd_line_value(w.rrd.path(),int(start),int(end),v)
            for i in range(0,len(dataTemp),60):
                for d in dataTemp[i:i+60]:
                    count = 0;total = 0.0
                    if d != None:
                        count += 1
                        total += d
                if total != 0:w.line.append(total / count)
                else:w.line.append(0)
    return render_to_response("html/report_availability_trend_perf.html",locals())

def get_widget_alert_times(widget,start,end):
    result = {"error":0,"warning":0,"ok":0,"all":0}
    field_def = {}
    if widget.data_def:
        try:
            current = rrdtool.fetch(widget.rrd.path(), "-s", str(start) + "-1", "-e", str(end), "LAST")
            data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
            ds = current[1]
            for i in range(0, len(ds)):
                if data_def.has_key(ds[i]):
                    field_def[i] = data_def[ds[i]]
            flag = False; flat = True
            for l in current[2]:
                tmp = False
                for x,y in field_def.items():
                    if eval(str(l[x])+y[2]):
                        tmp = True
                if tmp:
                    flag = True
                else:
                    flag = False
                    flat = True
                if flag  and flat:
                    result["error"] += 1
                    flat = False
        except:
            pass
    return result

@login_required()
def availability_trends_alert(request):
    projects = Project.objects.all().order_by("name")
    if "p" in request.GET:
        project = int(request.GET["p"])
        widgets = Widget.objects.filter(project=project)
    else:widgets = []
    defaultShowDays = 3
    ls = [];lsData = {}
    now = int(time.time())
    startTime = time.strftime("%Y-%m-%d",time.localtime(now - now % 86400 - 86400 * (defaultShowDays - 1)))
    endTime = time.strftime("%Y-%m-%d",time.localtime(now - now % 86400))
    for i in range(defaultShowDays):
        end = now - now % 86400 - 86400 * i
        start = end - 86400
        result = {}
        for w in widgets:
            if w.category:
                data = get_widget_alert_times(w,start,end)
                errorCount = data["error"]
                if w.category.title in result:result[w.category.title] += errorCount
                else:result[w.category.title] = errorCount
        for x,y in result.items():
            if x in lsData:lsData[x].append(y)
            else:lsData[x] = [y]
    for x,y in lsData.items():
        ls.append({"category":x,"line":y})
    ls = sorted(ls,key=lambda k:k["line"][0],reverse = True)
    return render_to_response("html/report_availability_trend_alert.html",locals())
