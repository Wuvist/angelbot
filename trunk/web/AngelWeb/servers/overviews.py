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
    label = RemarkLog.objects.filter(type=2).order_by("-id")[0]
    remarkLogs = RemarkLog.objects.filter(type=2,label=label.label)
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
        data = remarkLogs.filter(mark__in=servers).values("sign").annotate(count=Count("sign"))
        serverDict = {"ok":0,"warning":0,"error":0,"allProblem":0,"allType":0}
        for d in data:
            if d["sign"] == "Normal":serverDict["ok"] = d["count"]
            elif d["sign"] == "Unstable":serverDict["warning"] = d["count"]
            else:serverDict["error"] = d["count"]
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
    label = RemarkLog.objects.filter(type=2).values("label").annotate().order_by("-id")[1]
    serverDict = cache.get("serverDict_"+label["label"])
    if serverDict != None:
        cache.set("get_server_data_serverDict",serverDict,settings.CACHE_TIME)
        return serverDict
    serverDict = {"ok":0,"warning":0,"error":0,"allProblem":0,"allType":0}
    data = RemarkLog.objects.filter(type=2,label=label["label"]).values("sign").annotate(count=Count("sign"))
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

    return render_to_response('html/main.html') 
    
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
    t = datetime.now() - RemarkLog.objects.filter(type=2).order_by("-id")[0].created_time
    return render_to_response('html/top.html',{"request":request,"serverUpdate":t.days*86400+t.seconds,"tickets":ticketDict,"servers":serverDict,"services":servicesDict,"widgetStatus":widgetConfDifCount})
    
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

@login_required
@cache_page(settings.CACHE_TIME)
def problem_service(request,did):
    if not request.user.is_staff:
        raise Http404
    servers  = Server.objects.filter(power_on="Y").values_list("id",flat=True)
    for i in settings.EXCLUDE_IPS:
        servers = servers.exclude(ip__contains=i.replace("*",""))
    def get_server_info(w):
        try:
            if w.server.id not in servers:w.serverInfo = {"sign":"Unknown"}
            else:w.serverInfo = RemarkLog.objects.filter(mark=w.server.id,type=2).order_by("-id")[0]
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
