# -*- coding: utf-8 -*-
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
import time

@login_required()
def show(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    cmds = server.severcmd_set.all()
    c = RequestContext(request, 
        {"server":server,
        "cmds":cmds
        })
    return render_to_response('servers/show.html',c)

@login_required()
def show_cmd(request, server_id, cmd_id):
    server = get_object_or_404(Server, id=server_id)
    cmd = get_object_or_404(Cmd, id=cmd_id)
    c = RequestContext(request, 
        {"server":server,
        "cmd":cmd
        })
    return render_to_response('servers/show_cmd.html',c)

@login_required()
@cache_page(55) 
def dashboard_show(request, dashboard_id):
    import time
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)
    if not request.user.is_superuser:
        try:
            dashboard.user.get(id = request.user.id)
        except ObjectDoesNotExist:
            raise Http404
    
    alarmlogs = AlarmLog.objects.filter(created_on__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-created_on")
    frequentAlarmLogs = FrequentAlarmLog.objects.filter(lasterror_time__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-lasterror_time")
    showAlarms = False
    if len(alarmlogs)+len(frequentAlarmLogs) > 0 and int(dashboard_id) == 1:
        showAlarms = True
    c = RequestContext(request, 
        {"dashboard":dashboard,
        "alarmlogs":alarmlogs,
        "showAlarms":showAlarms,
        "frequentAlarmLogs":frequentAlarmLogs,
        })
    return render_to_response('servers/show_dashboard.html',c)

@login_required()
def dashboard_show_error(request,dashboard_error_id):
    import time
    dashboard_error = get_object_or_404(DashboardError, id=dashboard_error_id)
    imgs = dashboard_error.graphs.all()
    startTime = int(time.mktime(datetime.strptime(time.strftime("%Y-%m-%d",time.localtime()),"%Y-%m-%d").timetuple()))
    endTime = startTime + 86400
    if not request.user.is_superuser:
        try:
            dashboard_error.user.get(id = request.user.id)
        except ObjectDoesNotExist:
            raise Http404
    
    alarmlogs = AlarmLog.objects.filter(created_on__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-created_on")
    showAlarms = False
    if len(alarmlogs) >0 and int(dashboard_error.dashboard.id) == 1:
        showAlarms = True
    c = RequestContext(request, 
        {"dashboard":dashboard_error.dashboard,
        "dashboard_error":dashboard_error,
        "imgsDivWidth":dashboard_error.width*2+5,
        "alarmlogs":alarmlogs,
        "showAlarms":showAlarms,
        "startTime":startTime,
        "endTime":endTime,
        "imgs":imgs,
        "ticket":Ticket.objects.values("status").annotate(count=Count("status"))
        })
    return render_to_response('servers/show_dashboard_error.html',c)

@login_required()
def show_assort_widget(request):
    import time
    dashboard_id = 1
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)
    if not request.user.is_superuser:
        try:
            dashboard.user.get(id = request.user.id)
        except ObjectDoesNotExist:
            raise Http404
    
    alarmlogs = AlarmLog.objects.filter(created_on__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-30*60))).order_by("widget","-created_on")
    showAlarms = False
    if len(alarmlogs) >0 and int(dashboard_id) == 1:
        showAlarms = True
    c = RequestContext(request, 
        {"dashboard":dashboard,
        "alarmlogs":alarmlogs,
        "showAlarms":showAlarms,
        })
    return render_to_response('servers/show_assort_widget.html',c)

@login_required()
def execute_cmd(request, server_id, cmd_id):
    server = get_object_or_404(Server, id=server_id)
    cmd = get_object_or_404(Cmd, id=cmd_id)
    
    def fetch_page (url):
        import urllib2
        data = None
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        result = response.read()
        return result
    log = CmdLog()
    log.user = request.user
    log.cmd = server.name + ": " + cmd.text
    log.save()
    from django.utils.http import urlencode as django_urlencode
    url = settings.BOT_URL + django_urlencode({"host": server.ip, "cmd":cmd.text})
    result = fetch_page(url)
    log.result = result
    log.save()

    return HttpResponse(fetch_page(url))

def rrd_img(request, widget_id):
    import time
    widget = get_object_or_404(Widget, id=widget_id)
    from subprocess import Popen, PIPE
    width = request.GET["width"]
    height = request.GET["height"]
    start = request.GET["start"]
    end = request.GET["end"]
    check_lines = eval(request.GET["cl"])
    # TODO should refactor here
    def get_line(widget):
        return widget.graph_def.replace("{rrd}", settings.RRD_PATH + widget.rrd.name + ".rrd").replace("\n", "").replace("\r", " ")
    def get_line_diff(widget, diff):
        def update_def(line):
            line = line.strip()
            if line.startswith("DEF:"):
                pos = line.index("=", 4)
                name = line[4:pos]
                if diff == "1d":
                    shift = " SHIFT:" + diff[1:] + name + ":86400"
                if diff == "1w":
                    shift = " SHIFT:" + diff[1:] + name + ":604800"
                return line[0:4] + diff[1:] + line[4:] + ":start=%s-%s:end=%s" % (start, diff, end.replace("s+", "start+")) + shift
            if line.startswith("LINE:"):
                pos = line.index(":")
                color = line.index("#")
                if diff == "1d":
                    return line[0:pos] + ":" + diff[1:] + line[pos+1:color] + "#fbba5c:Yesterday"
                else:
                    return line[0:pos] + ":" + diff[1:] + line[pos+1:color] + "#b5b5b5:LastWeek"

        graph_def = widget.graph_def.split("\n")
        graph_def = map(update_def, graph_def)

        return (" ".join(graph_def)).replace("{rrd}", settings.RRD_PATH + widget.rrd.name + ".rrd")
    
    #line = get_line(widget)
    #if request.GET.has_key("1d"):
    #    line += " " + get_line_diff(widget, "1d")    
    #if request.GET.has_key("1w"):
    #line += " " + get_line_diff(widget, "1w")

    def get_check_lines(line_diff,get_time,withTime="",shiftTime=""):
        color = get_line(widget)[get_line(widget).index("LINE:"+line_diff)+5+len(line_diff):get_line(widget).index("LINE:"+line_diff)+len(line_diff)+12] #5+7
        line = "DEF:"+line_diff+"="+settings.RRD_PATH + widget.rrd.name + ".rrd:"+line_diff+":LAST LINE:"+line_diff+color+":"+line_diff.capitalize()
        if get_time == "withAnyDate":
            startWithTime = int(time.mktime(time.strptime(request.GET["withDate"], "%Y-%m-%d")))
            line += " " + "DEF:donline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+str(startWithTime)+\
            ":end=start+1d SHIFT:donline:"+str(int(shiftTime)-startWithTime)+" LINE:donline#fbba5c:"+withTime
        elif get_time == "1d":
            line += " " + "DEF:donline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+start+"-"+get_time+":end=start+1d SHIFT:donline:86400 LINE:donline#fbba5c:Yesterday"
        elif get_time == "1w":
            one_day = " " + "DEF:donline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+start+"-1d:end=start+1d SHIFT:donline:86400 LINE:donline#fbba5c:Yesterday"
            line += one_day + " " + "DEF:wonline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+start+"-"+get_time+":end=start+1d SHIFT:wonline:604800 LINE:wonline#b5b5b5:LastWeek"
        return line
    
    if check_lines == []:
        line = get_line(widget)
    elif request.GET.has_key("withAnyDate"):
        line =get_check_lines(check_lines[0],"withAnyDate",request.GET["withDate"],start)
    elif request.GET.has_key("1w"):
        line =get_check_lines(check_lines[0],"1w")
    elif request.GET.has_key("1d"):
        line =get_check_lines(check_lines[0],"1d")
    else:
        line = ""
        for lines in check_lines:
            line +=" " + get_check_lines(lines,"")
    cmd = 'rrdtool graph - -E --imgformat PNG -s %s -e %s --width %s --height %s %s' % (
        start, end, width, height, line)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    
    if len(stderr) > 0:
        response = HttpResponse(cmd + "\n" + stderr)
        response["content-type"] = "text/plain"
        return response
    response = HttpResponse(stdout)
    response["content-type"] = "image/png"
    return response

def rrd_download(request, rrd_id):
    rrd = get_object_or_404(Rrd, id=rrd_id)
    from subprocess import Popen, PIPE
    import time
    start = str(int(time.mktime(datetime.strptime(request.GET["start"], "%Y-%m-%d").timetuple())))
    end = str(int(time.mktime(datetime.strptime(request.GET["end"], "%Y-%m-%d").timetuple())))

    if start == end:
        end = "start+1d"
 
    line = settings.RRD_PATH  + rrd.name + ".rrd"

 
    cmd = 'rrdtool fetch %s LAST -s %s -e %s' % (line, start, end)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if len(stderr) > 0:
        response = HttpResponse(cmd + "\n" + stderr)
        response["content-type"] = "text/plain"
        return response
    ls = stdout.split("\n")

    def process_header(line):
        data = line.split(" ")
        result = ["date"]
        for item in data:
            if item:
                result.append(item)
        return ",".join(result)

    ls[0] = process_header(ls[0])
    
    def process_line(line):
        if not line:
            return ""
        
        data = line.split(" ")
        data[0] = datetime.fromtimestamp(int(data[0][:-1])).strftime("%Y-%m-%d %H:%M")
        for i in range(1, len(data)):
            if data[i] == 'nan':
                data[i] = ""
            else:
                data[i] = str(float(data[i]))
        return ",".join(data)
    
    for i in range(1, len(ls)):
        ls[i] = process_line(ls[i])
        
    response = HttpResponse(ls[0] + "\n".join(ls[1:]))
    
    response["content-type"] = "text/csv"
    response["content-disposition"] = "attachment; filename=" + rrd.name + "_" +  request.GET["start"] + "_" + request.GET["end"] + ".csv"
    return response

# rrd related features
# should make it a saparat app?
# integrate it with Django admin?

@login_required()
def rrd_list(request):
    c = RequestContext(request, 
        {"rrds":Rrd.objects.all()
        })
    return render_to_response('servers/rrd_list.html',c)
    
@login_required()
def rrd_create(request, rrd_id):
    rrd = get_object_or_404(Rrd, id=rrd_id)
    from subprocess import Popen, PIPE
    import time
    start_time = '2010-06-01 00:00'
    start_time = time.strptime(start_time, "%Y-%m-%d %H:%M")
    start_time = int(time.mktime(start_time))
    
    cmd = 'rrdtool create %s --start %d %s' % (settings.RRD_PATH + rrd.name + ".rrd", start_time, rrd.setting.replace("\n", "").replace("\r", " "))
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return HttpResponseRedirect("/rrd/")
    
@login_required()
def rrd_show(request, rrd_id):
    rrd = get_object_or_404(Rrd, id=rrd_id)
    
    # import rrdtool
    # path = settings.RRD_PATH + rrd.name + ".rrd"
    # info = rrdtool.info(str(path))
    # 
    # for key in info.keys:
    #     
    # 
    # c = RequestContext(request, 
    #     {"rrd":rrd,
    #     "info": str(stdout)
    #     })
    
    from subprocess import Popen, PIPE
    cmd = 'rrdtool info %s' % (settings.RRD_PATH + rrd.name + ".rrd")
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    
    c = RequestContext(request, 
        {"rrd":rrd,
        "info": stdout + stderr
        })
    return render_to_response('servers/rrd_show.html',c)
    
@login_required()
def rrd_show_widget_graph(request, dashboard_id, widget_id):
    import re
    import time
    lines = []
    check_lines = []
    widget = get_object_or_404(Widget, id=widget_id)
    rrd = get_object_or_404(Rrd, id=widget.rrd.id)
    line = widget.graph_def.replace("{rrd}", settings.RRD_PATH + widget.rrd.name + ".rrd").replace('\n','')
    lines = re.compile( "LINE:(\w+)" ).findall(line)
    end = "s%2b1d"
    graph_option = ""
    
    if request.GET.has_key("date"):
        show_date = request.GET["date"]
    else:
        show_date = time.strftime("%Y-%m-%d")
    
    if request.GET.has_key("withdate"):
        withdate = request.GET["withdate"]
    else:
        withdate = time.strftime("%Y-%m-%d")
        
    if request.GET.has_key("show1d"):
        graph_option += "&1d=1"

    if request.GET.has_key("show1w"):
        graph_option += "&1w=1&1d=1"
    
    if request.GET.has_key("withAnyDate"):
        graph_option += "&withAnyDate=True"
        
    for checkbox in lines:
        if request.GET.has_key(checkbox):
            check_lines.append(checkbox)

    start_time = show_date + ' 00:00'
    start_time = time.strptime(start_time, "%Y-%m-%d %H:%M")
    start_time = int(time.mktime(start_time))
    start = start_time
    check_line_values = []
    
    class check_line_value(object):
        def __init__(self, line, checked):
            self.line = line
            self.checked = checked
            
    for line in lines:
        if line in check_lines:
            check_line_values.append(check_line_value(line, " checked"))
        else:
            check_line_values.append(check_line_value(line, " "))
    
    if lines == check_lines or len(lines)==1:
        checkall = "checked"
        check_line_values[0]=(check_line_value(lines[0], " checked"))
    else:
        checkall = ""
    
    c = RequestContext(request,
        {"rrd":rrd,
        "dashboard_id":dashboard_id,
        "widget": widget,
        "show_date" : show_date,
        "start": start,
        "end": end,
        "graph_option":graph_option,
        "lines":lines,
        "check_lines":check_lines,
        "check_line_values": check_line_values,
        "checkall":checkall,
        "withdate":withdate,
        })
    return render_to_response('servers/rrd_show_graph.html',c)

def parser(request):
    import matplotlib
    matplotlib.use('Agg')
    import numpy as np
    import time
    import rrdtool
    from cStringIO import StringIO
    from matplotlib import pyplot as plt
    from subprocess import Popen, PIPE

    def get_rrd_data(widget_id,start,end):
        widget = get_object_or_404(Widget,id = widget_id)
        rrd_name = widget.rrd.name
        cmd = "rrdtool fetch " + widget.rrd.path() + " LAST -s " + str(start) +" -e " + str(end)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        data_ls = [x.split(" ") for x in stdout.replace(":","").replace("  ","").replace("n","-").replace("N","-").replace("\r","\n").split("\n") ]
        return data_ls
    
    def parser_time(data_ls,line_number,start_time_number):
        result = []
        total = 0
        x = 0.0000000000001
        time_def = time.strftime("%Y%m%d%H%M%S",time.localtime(int(data_ls[3][0])))[:start_time_number]
        last_time = data_ls[-2][0]
        for i in data_ls:
            try:
                times = time.strftime("%Y%m%d%H%M%S",time.localtime(int(i[0])))
                if i[0] == last_time:
                    average = total / x
                    result.append(average)
                elif times[:start_time_number] == time_def:
                    total += float(i[line_number])
                    x += 1
                else:
                    time_def = times[:start_time_number]
                    average = total / x
                    try:
                        x = 1.0
                        total = float(i[line_number])
                    except:
                        total = 0
                        x = 0.0000000000001
                    result.append(average)
            except:
                 pass
        
        return result
    
    def parser_week(rrd_lines,check_lines,widgetls):
        def avaerge_week(data_ls,line_number):
            result = []
            total = 0
            j = 10320
            x = 0.0000000000001
            data_ls_count = len(data_ls)
            for i in range(data_ls_count):
                try:
                    if i == data_ls_count - 2:
                        average = total / x
                        result.append(average)
                        break
                    elif i < j:
                        total += float(data_ls[i][line_number])
                        x += 1
                    else:
                        average = total / x
                        j += 10080
                        try:
                            x = 1.0
                            total = float(data_ls[i][line_number])
                        except:
                            total = 0
                            x = 0.0000000000001
                        result.append(average)
                except:
                     pass
            return result
        
        def parser_start(rrd_lines,check_lines,data_ls):
            
            list_all = []
            for i in range(0,len(rrd_lines)):
                if rrd_lines[i] in check_lines:
                    list_all.append(avaerge_week(data_ls, i+1))
            
            return list_all
        
        def start_week(rrd_lines,check_lines,widgetls):
            list_all = []
            times_ls = []
            if len(widgetls)==1:
                data_ls = get_rrd_data(widgetls[0],start,end)
                list_all=parser_start(rrd_lines,check_lines,data_ls)
            else:
                for p_widget_id in widgetls:
                    data_ls = get_rrd_data(p_widget_id,start,end)
                    list_all.append(parser_start(rrd_lines,check_lines,data_ls)[0])
            
            j = 10320
            data_ls_count = len(data_ls)
            for i in range(data_ls_count):
                try:
                    #if i == data_ls_count - 2:
                    if i == 3:
                        times_ls.append(time.strftime("%Y-%m-%d",time.localtime(int(data_ls[i][0])-60)))
                    elif i == j:
                        times_ls.append(time.strftime("%Y-%m-%d",time.localtime(int(data_ls[i][0]))))
                        j += 10080
                except:
                    pass
            list_all.append(times_ls)
            
            return list_all
        return start_week(rrd_lines,check_lines,widgetls)

    def parser_start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x):
        list_all = []
        
        for i in range(0,len(rrd_lines)):
            if rrd_lines[i] in check_lines:
                list_all.append(parser_time(data_ls, i+1, start_time_number))
    
        return list_all
    
    def start_parse(widgetls,rrd_lines,check_lines,start_time_number,p_last_time,time_x):
        result = []
        result_widget = []
        if len(widgetls)==1:
            data_ls = get_rrd_data(widgetls[0],start,end)
            result=parser_start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x)
        else:
            for p_widget_id in widgetls:
                data_ls = get_rrd_data(p_widget_id,start,end)
                result.append(parser_start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x)[0])
        times_ls = []
        time_def = time.strftime("%Y%m%d%H%M%S",time.localtime(int(data_ls[3][0])))[:start_time_number]
        last_time = data_ls[-2][0]
        for i in data_ls:
            try:
                times = time.strftime("%Y%m%d%H%M%S",time.localtime(int(i[0])))
                if i[0] == last_time:
                    times_ls.append(eval(p_last_time))
                elif times[:start_time_number] > time_def:
                    time_def = times[:start_time_number]
                    times_ls.append(eval(time_x))
            except:
                pass
        result.append(times_ls)
        return result

    widgetls = request.GET["widgetls"].split(",")
    widgetls_name = map(lambda x:get_object_or_404(Widget,id = x).title,widgetls)
    widget = get_object_or_404(Widget,id = widgetls[0])
    check_lines = request.GET["cl"].split(',')
    start = int(time.mktime(datetime.strptime(request.GET["start"], "%Y-%m-%d^%H:%M:%S").timetuple()))
    end = int(time.mktime(datetime.strptime(request.GET["end"], "%Y-%m-%d^%H:%M:%S").timetuple()))
    rrd_lines = rrdtool.fetch(widget.rrd.path(), "-s", str(2), "-e", "s+0", "LAST")[1]
    if start == end:
        start -= 86400
    start -= 60

    if check_lines == ['']:
        check_lines = rrd_lines
    if len(widgetls)>1:
        check_lines = [check_lines[0]]
        img_legend = widgetls_name
        img_title = (request.GET["start"]+" _ "+request.GET["end"]+" _ "+widget.category.title+" - "+check_lines[0]+"   /"+request.GET["ptime"]).replace("^"," ")
    else:
        img_legend = check_lines
        img_title = (request.GET["start"]+" _ "+request.GET["end"]+" _ "+widget.category.title+" - "+widget.title+"   /"+request.GET["ptime"]).replace("^"," ")
    
    if request.GET["ptime"] =="hour":
        start_time_number = 10
        p_last_time = 'time.strftime("%m-%d %H:%M",time.localtime(int(i[0])-60))[:-2]+"00"'
        time_x = 'time.strftime("%m-%d %H:%M",time.localtime(int(i[0])-3600))'
        result = start_parse(widgetls,rrd_lines,check_lines,start_time_number,p_last_time,time_x)
    elif request.GET["ptime"] =="day":
        start_time_number = 8
        p_last_time = 'time.strftime("%Y-%m-%d",time.localtime(int(i[0])-60))'
        time_x = 'time.strftime("%Y-%m-%d",time.localtime(int(i[0])-86400))'
        result = start_parse(widgetls,rrd_lines,check_lines,start_time_number,p_last_time,time_x)
    elif request.GET["ptime"] == "week":
        result = parser_week(rrd_lines,check_lines,widgetls)
    else:
        start_time_number = 6
        p_last_time = 'time.strftime("%Y-%m", time.localtime(int(i[0])-60))'
        time_x = 'time.strftime("%Y-%m",time.localtime(int(i[0])-2419200))'
        result = start_parse(widgetls,rrd_lines,check_lines,start_time_number,p_last_time,time_x)

    x_values = []
    if len(result[-1]) >= 18:
        interval = len(result[-1])/9
        for i in range(0, len(result[-1]), interval):
            x_values.append(result[-1][i])
    else:
        x_values = result[-1]
        interval = 1

    fig = plt.figure(figsize=(20,9))
    ax = fig.add_axes([0.05,0.1,0.9,0.8])
    for i in range(len(result)-1):
        ax.plot(result[i])
    
    ax.legend(img_legend, loc="upper right", shadow=True)
    ax.set_xticks(np.arange(0,len(result[-1]),interval))
    ax.set_xticklabels(x_values)
    ax.set_title(img_title)
    ax.grid(True)
    fig.autofmt_xdate()
    pic_buf = StringIO()
    fig.savefig(pic_buf,dpi=65)
    image_data = pic_buf.getvalue()
    pic_buf.close()
    fig.clear()
    plt.close()
    
    response = HttpResponse(image_data)
    response["content-type"] = "image/png"
    return response

def parse_downoad(request):
    from subprocess import Popen, PIPE
    import time
    import rrdtool

    def get_rrd_data(widget_id,start,end):
        widget = get_object_or_404(Widget,id = widget_id)
        rrd_name = widget.rrd.name
        cmd = "rrdtool fetch " + widget.rrd.path() + " LAST -s " + str(start) +" -e " + str(end)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        data_ls = [x.split(" ") for x in stdout.replace(":","").replace("  ","").replace("n","-").replace("N","-").replace("\r","\n").split("\n") ]
        return data_ls
    
    def parser_time(widget_name,data_ls, rrd_lines, line_number,start_time_number):
        result = [widget_name+"-"+rrd_lines[line_number-1]]
        total = 0
        x = 0.0000000000001
        time_def = time.strftime("%Y%m%d%H%M%S",time.localtime(int(data_ls[3][0])))[:start_time_number]
        last_time = data_ls[-2][0]
        for i in data_ls:
            try:
                times = time.strftime("%Y%m%d%H%M%S",time.localtime(int(i[0])))
                if i[0] == last_time:
                    average = total / x
                    result.append(str('%.4f' % average))
                elif times[:start_time_number] == time_def:
                    total += float(i[line_number])
                    x += 1
                else:
                    time_def = times[:start_time_number]
                    average = total / x
                    try:
                        x = 1.0
                        total = float(i[line_number])
                    except:
                        total = 0
                        x = 0.0000000000001
                    result.append(str('%.4f' % average))
            except:
                 pass
        
        return result

    def start_parse(get_parse_time,dashboard_id,category,start_time_number,p_last_time,time_x):
        result = []
        widgetls = map(lambda x:x["id"],Widget.objects.filter(dashboard=int(dashboard_id)).filter(category=category.replace("---","")).values("id","title").order_by("title"))
        rrd_lines = rrdtool.fetch(get_object_or_404(Widget,id = widgetls[0]).rrd.path(), "-s", str(2), "-e", "s+0", "LAST")[1]
        for p_widget_id in widgetls:
            data_ls = get_rrd_data(p_widget_id,start,end)
            widget_name = get_object_or_404(Widget,id=p_widget_id).title
            ls_widget = []
            for line_number in range(0,len(rrd_lines)):
                ls_widget.append(parser_time(widget_name,data_ls, rrd_lines, line_number+1, start_time_number))
            result.append(ls_widget)
        if get_parse_time:
            times_ls = ["date"]
            time_def = time.strftime("%Y%m%d%H%M%S",time.localtime(int(data_ls[3][0])))[:start_time_number]
            last_time = data_ls[-2][0]
            for i in data_ls:
                try:
                    times = time.strftime("%Y%m%d%H%M%S",time.localtime(int(i[0])))
                    if i[0] == last_time:
                        times_ls.append(eval(p_last_time))
                    elif times[:start_time_number] > time_def:
                        time_def = times[:start_time_number]
                        times_ls.append(eval(time_x))
                except:
                    pass
            result.append(times_ls)
        return result

    def parser_week(get_parse_time,categorys,dashboard_id):
         def avaerge_week(widget_name,rrd_lines,data_ls,line_number):
             result = [widget_name+"-"+rrd_lines[line_number-1]]
             total = 0
             j = 10320
             x = 0.0000000000001
             data_ls_count = len(data_ls)
             for i in range(data_ls_count):
                 try:
                     if i == data_ls_count - 2:
                         average = total / x
                         result.append(str('%.4f' % average))
                         break
                     elif i < j:
                         total += float(data_ls[i][line_number])
                         x += 1
                     else:
                         average = total / x
                         j += 10080
                         try:
                             x = 1.0
                             total = float(data_ls[i][line_number])
                         except:
                             total = 0
                             x = 0.0000000000001
                         result.append(str('%.4f' % average))
                 except:
                      pass
             return result
         
         def start_week(get_parse_time,category,dashboard_id):
             result = []
             widgetls = map(lambda x:x["id"],Widget.objects.filter(dashboard=int(dashboard_id)).filter(category=category.replace("---","")).values("id","title").order_by("title"))
             rrd_lines = rrdtool.fetch(get_object_or_404(Widget,id = widgetls[0]).rrd.path(), "-s", str(2), "-e", "s+0", "LAST")[1]
             for p_widget_id in widgetls:
                 data_ls = get_rrd_data(p_widget_id,start,end)
                 widget_name = get_object_or_404(Widget,id=p_widget_id).title
                 ls_widget = []
                 for line_number in range(0,len(rrd_lines)):
                     ls_widget.append(avaerge_week(widget_name,rrd_lines,data_ls, line_number+1))
                 result.append(ls_widget)
             if get_parse_time:
                times_ls = ["date"]
                j = 10320
                data_ls_count = len(data_ls)
                for i in range(data_ls_count):
                    try:
                        #if i == data_ls_count - 2:
                        if i ==  3:
                            times_ls.append(time.strftime("%Y-%m-%d",time.localtime(int(data_ls[i][0])-60)))
                        elif i == j:
                            times_ls.append(time.strftime("%Y-%m-%d",time.localtime(int(data_ls[i][0]))))
                            j += 10080
                    except:
                        pass
                result.append(times_ls)
             return result
         return start_week(get_parse_time,categorys,dashboard_id)

    def order_by_widget(parse_week,check_categorys,dashboard_id,start_time_number,p_last_time,time_x):
        data = ''
        category_time = 0
        get_parse_time = False
        for category in check_categorys:
            category_time += 1
            if category_time != len(check_categorys):
                data += category + '\n'
                if parse_week == "week":
                    result = parser_week(get_parse_time,category,dashboard_id)
                else:
                    result = start_parse(get_parse_time,dashboard_id,category,start_time_number,p_last_time,time_x)
                for i in result:
                    for x in i:
                        data += ','.join(x)+'\n'
                    data +='\n'
            else:
                get_parse_time = True
                data += category+'\n'
                if parse_week == "week":
                    result = parser_week(get_parse_time,category,dashboard_id)
                else:
                    result = start_parse(get_parse_time,dashboard_id,category,start_time_number,p_last_time,time_x)
                for i in result[:-1]:
                    for x in i:
                        data += ','.join(x)+'\n'
                    data +='\n'
        data = ','.join(result[-1])+'\n' + data
        return data

    def order_by_widget_value(parse_week,check_categorys,dashboard_id,start_time_number,p_last_time,time_x):
        data = ''
        category_time = 0
        get_parse_time = False
        for category in check_categorys:
            category_time += 1
            if category_time != len(check_categorys):
                data += category + '\n'
                if parse_week == "week":
                    result = parser_week(get_parse_time,category,dashboard_id)
                else:
                    result = start_parse(get_parse_time,dashboard_id,category,start_time_number,p_last_time,time_x)
                for y in range(len(result[0])):
                    for i in result:
                        data += ','.join(i[y])+'\n'
                    data += '\n'
            else:
                get_parse_time = True
                data += category + '\n'
                if parse_week == "week":
                    result = parser_week(get_parse_time,category,dashboard_id)
                else:
                    result = start_parse(get_parse_time,dashboard_id,category,start_time_number,p_last_time,time_x)
                for y in range(len(result[0])):
                    for i in result[:-1]:
                        data += ','.join(i[y]) + '\n'
                    data += '\n'
        data = ','.join(result[-1])+'\n' + data
        return data
    
    dashboard_id = request.GET["dashboard_id"]
    if request.GET.has_key("cdc"):
        check_categorys = map(lambda x:x.replace("&nbsp"," "),request.GET.getlist("cdc"))
    else:
        check_categorys = [Widget.objects.filter(dashboard=dashboard_id).values("category").order_by('category')[0]["category"]]
    
    start = int(time.mktime(datetime.strptime(request.GET["start"]+"^"+request.GET["start1"], "%Y-%m-%d^%H:%M:%S").timetuple()))
    end = int(time.mktime(datetime.strptime(request.GET["end"]+"^"+request.GET["end1"], "%Y-%m-%d^%H:%M:%S").timetuple()))
    if start == end:
        start -= 86400
    start -= 60
    
    if request.GET["ptime"] =="hour":
        start_time_number = 10
        p_last_time = 'time.strftime("%Y-%m-%d %H:%M",time.localtime(int(i[0])-60))[:-2]+"00"'
        time_x = 'time.strftime("%Y-%m-%d %H:%M",time.localtime(int(i[0])-3600))'
        if request.GET["order"]=="1":
            data = order_by_widget("",check_categorys,dashboard_id,start_time_number,p_last_time,time_x)
        else:
            data = order_by_widget_value("",check_categorys,dashboard_id,start_time_number,p_last_time,time_x)
    elif request.GET["ptime"] =="day":
        start_time_number = 8
        p_last_time = 'time.strftime("%Y-%m-%d",time.localtime(int(i[0])-60))'
        time_x = 'time.strftime("%Y-%m-%d",time.localtime(int(i[0])-86400))'
        if request.GET["order"]=="1":
            data = order_by_widget("",check_categorys,dashboard_id,start_time_number,p_last_time,time_x)
        else:
            data = order_by_widget_value("",check_categorys,dashboard_id,start_time_number,p_last_time,time_x)
        
    elif request.GET["ptime"] == "week":
        if request.GET["order"] == "1":
            data = order_by_widget("week",check_categorys,dashboard_id,"","","")
        else:
            data = order_by_widget_value("week",check_categorys,dashboard_id,"","","")
    else:
        start_time_number = 6
        p_last_time = 'time.strftime("%Y-%m", time.localtime(int(i[0])-60))'
        time_x = 'time.strftime("%Y-%m",time.localtime(int(i[0])-2419200))'
        if request.GET["order"]=="1":
            data = order_by_widget("",check_categorys,dashboard_id,start_time_number,p_last_time,time_x)
        else:
            data = order_by_widget_value("",check_categorys,dashboard_id,start_time_number,p_last_time,time_x)
        
    response = HttpResponse(data)
    response["content-type"] = "text/csv"
    response["content-disposition"] = "attachment; filename="+request.GET["start"]+"~"+request.GET["end"]+"_"+"mozat_angel_"+request.GET["ptime"]+".csv"
    return response

@login_required()
def show_parse_graph(request,dashboard_id, widget_id):
    import re
    import time
    
    if str(dashboard_id) not in map(lambda x:str(x["id"]),Dashboard.objects.filter(user = request.user.id).values("id")):raise Http404   
    widget = get_object_or_404(Widget, id=widget_id)
    
    widgetCategory = []
    class check_category_values(object):
        def __init__ (self,x):
            self.name = x.title
            self.value = x.id
    for x in WidgetCategory.objects.filter(widget__in = Widget.objects.values('id').filter(dashboard=dashboard_id)).annotate():
        widgetCategory.append(check_category_values(x))
    line = widget.graph_def.replace("{rrd}", widget.rrd.path()).replace('\n','').replace('\r','')
    lines = re.compile( "LINE:(\w+)" ).findall(line)
    
    if request.GET.has_key("start"):
        start = request.GET["start"]
    else:
        start = time.strftime("%Y-%m-%d")
    if request.GET.has_key("start1"):
        start1 = request.GET["start1"]
    else:
        start1 = time.strftime("%H:%M:%S")
        
    if request.GET.has_key("end"):
        end = request.GET["end"]
    else:
        end = time.strftime("%Y-%m-%d")
    if request.GET.has_key("end1"):
        end1 = request.GET["end1"]
    else:
        end1 = time.strftime("%H:%M:%S")
        
    if request.GET.has_key("ptime"):
        ptime = request.GET["ptime"]
    else:
        ptime = "hour"    
    
    warn_start = int(time.mktime(datetime.strptime(start + start1, "%Y-%m-%d%H:%M:%S").timetuple()))
    warn_end = int(time.mktime(datetime.strptime(end + end1, "%Y-%m-%d%H:%M:%S").timetuple()))
    
    if warn_start - warn_end > 0:
        warn = "<div class='errornote'>The end time must be longer than start time or equals !</div>"
    else:
        warn = ""
    check_lines = []
    for checkbox in lines:
        if request.GET.has_key(checkbox):
            check_lines.append(checkbox)
        
    check_line_values = []
    class check_line_value(object):
        def __init__(self, line, checked):
            self.line = line
            self.checked = checked
    
    for line in lines:
        if line in check_lines:
            check_line_values.append(check_line_value(line, " checked"))
        else:
            check_line_values.append(check_line_value(line, " "))
            
    if lines == check_lines or len(lines)==1:
        checkall = "checked"
        check_line_values[0]=(check_line_value(lines[0], " checked"))
    else:
        checkall = ""
    check_lines = ','.join(check_lines)
    
    contrast_widgets = {}
    for i in Widget.objects.filter(category=widget.category).filter(dashboard=dashboard_id).values("title","id"):
        contrast_widgets[str(i['id'])] = i['title']
    widgets = []
    class check_widgets_values(object):
        def __init__ (self,name,value,checked):
            self.name = contrast_widgets[name]
            self.value = value
            self.checked = checked
    check_widgets_id = []
    for i in contrast_widgets.keys():
        if i in request.GET.getlist("check_widget"):
           check_widgets_id.append(i)
           widgets.append(check_widgets_values(i, i, " checked"))
        else:
           widgets.append(check_widgets_values(i, i, ""))
    if len(check_widgets_id)==len(contrast_widgets) or len(contrast_widgets)==1:
        checkWidgetAll = " checked"
        widgets[0]=(check_widgets_values(contrast_widgets.keys()[0],contrast_widgets.keys()[0]," checked"))
    else:
        checkWidgetAll = ""
    if check_widgets_id == [] or request.GET.get("showWidgets","") == "Show Date":check_widgets_id = [widget_id]
    widgets_title = map(lambda x:contrast_widgets[x],check_widgets_id)
    check_widgets_id = ','.join(check_widgets_id)
    widgets = sorted(widgets, key=lambda x:x.name)

    c = RequestContext(request,
        {"dashboard_id":dashboard_id,
        "widgets_title":widgets_title,
        "check_widgets_id":check_widgets_id,
        "start":start,
        "start1":start1,
        "end":end,
        "end1":end1,
        "ptime":ptime,
        "lines":lines,
        "check_lines":check_lines,
        "check_line_values": check_line_values,
        "checkall":checkall,
        "warn":warn,
        "widgets":widgets,
        "check_widgets_id":check_widgets_id,
        "checkWidgetAll":checkWidgetAll,
        "widgetCategory":widgetCategory,
        })
    return render_to_response('servers/rrd_parse.html',c)

def grah_aider_img(request,graphid,width,height,start_time,end_time):
    import re
    import time
    from subprocess import Popen, PIPE
    
    def get_line(graphAiderDef):
        return graphAiderDef.lines_def.replace("{rrd}", settings.RRD_PATH + graphAiderDef.rrd.name + ".rrd").replace("\n", "").replace("\r", " ")
    
    def get_check_lines(line_diff):
        color = get_line(graphAiderDef)[get_line(graphAiderDef).index("LINE:"+line_diff)+5+len(line_diff):get_line(graphAiderDef).index("LINE:"+line_diff)+len(line_diff)+12] #5+7
        line = "DEF:"+line_diff+"="+settings.RRD_PATH + graphAiderDef.rrd.name + ".rrd:"+line_diff+":LAST LINE:"+line_diff+color+":"+line_diff.capitalize()
        if graphAiderDef.graph_type == "2":
            one_day = " " + "DEF:donline="+settings.RRD_PATH+graphAiderDef.rrd.name+".rrd:"+line_diff+":LAST:start=start_time-1d:end=end_time-1d SHIFT:donline:86400 LINE:donline#fbba5c:Yesterday"
            line += one_day + " " + "DEF:wonline="+settings.RRD_PATH+graphAiderDef.rrd.name+".rrd:"+line_diff+":LAST:start=start_time-1W:end=end_time-1W SHIFT:wonline:604800 LINE:wonline#b5b5b5:LastWeek"
        return line
    
    graphAiderDef = get_object_or_404(GraphAiderDef,id=graphid)
    lines = re.compile( "LINE:(\w+)" ).findall(graphAiderDef.lines_def)
    if graphAiderDef.graph_type == "2":
        lines = lines[:1]
    line = ""
    for l in lines:
        line += " " + get_check_lines(l)
    
    cmd = ("rrdtool graph - -E --imgformat PNG -t \""+graphAiderDef.title+"\" -s start_time -e end_time --width "+width+" --height "+height+" "+line).replace("start_time",str(start_time)).replace("end_time",str(end_time))
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    
    if len(stderr) > 0:
        response = HttpResponse(cmd + "\n" + stderr)
        response["content-type"] = "text/plain"
        return response
    response = HttpResponse(stdout)
    response["content-type"] = "image/png"
    return response

def graph_aiders(request,aiderid):
    import time
    
    graph_aider = get_object_or_404(GraphAider,id=aiderid)
    graphs = graph_aider.graphs.all()
    def_time = time.strftime("%H:%M:%S")
    
    start = request.GET.get("start",time.strftime("%Y-%m-%d"))
    start1 = request.GET.get("start1","00:00:00")
    end = request.GET.get("end",time.strftime("%Y-%m-%d",time.localtime(time.time()+86400)))
    end1 = request.GET.get("end1","00:00:00")
    if request.GET.has_key("show7"):
        start = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))
        start1 = "07:00:00"
        end = time.strftime("%Y-%m-%d")
        end1 = "07:00:00"
    elif request.GET.has_key("showtoday") or start+start1 == end+end1:
        start = time.strftime("%Y-%m-%d")
        start1 = "00:00:00"
        end = time.strftime("%Y-%m-%d",time.localtime(time.time()+86400))
        end1 = "00:00:00"
        
    startTime = int(time.mktime(datetime.strptime(start + start1, "%Y-%m-%d%H:%M:%S").timetuple()))
    endTime = int(time.mktime(datetime.strptime(end + end1, "%Y-%m-%d%H:%M:%S").timetuple()))
    
    if startTime - endTime > 0:
        warn = "<div class='errornote'>The end time must be longer than start time or equals !</div>"
    else:
        warn = ""
    
    c = RequestContext(request,
        {"graphs":graphs,
        "width":graph_aider.width,
        "height":graph_aider.height,
        "start":start,
        "start1":start1,
        "end":end,
        "end1":end1,
        "warn":warn,
        "startTime":startTime,
        "endTime":endTime,
        "refresh_time":graph_aider.refresh_time*1000,
        })
    return render_to_response('servers/graph_aider.html',c)

    
def doCall():
    import telnetlib
    tn = telnetlib.Telnet(settings.RING_IP,settings.RING_PORT)
    tn.read_until("login: ")
    tn.write(settings.RING_USERNAME + "\r\n")
    tn.read_until("password:")
    tn.write(settings.RING_PASSWORD + "\r\n")
    tn.read_until(">")
    tn.write(settings.RING_PATH + "\r\n")
    result = tn.read_until(">")
    tn.write("exit\r\n")
    if "doneok" in result:
        return True
    else:
        return False

def alarm(request):
    import time
    from django.contrib.auth.models import User
    contact_users = {1:"firstcontact",2:"secondcontact",3:"thirdcontact",4:"fourthcontact",5:"fifthcontact",6:"sixthcontact"}
    def createTicket(errorType,widget,result,users,assign="no"):
        
        timeNow = '\''+str(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))+'\''
        ticketId = ""
        try:
            ticket = Ticket()
            ticket.widget = widget
            ticket.service = widget.service_type
            ticket.title = errorType + str(widget.title)
            ticket.recorder = User.objects.get(username="angel")
            ticket.status = "New"
            ticket.incident = result
            ticket.incidenttype = "---"
            ticket.save()
            for i in widget.project.all():
                ticket.project.add(i)
            ticketId = Ticket.objects.all().order_by("-id")[0].id
            result = ""
            contactReault = "suc"
        except:
            result = "created ticket failed !"
            contactReault = "fail"
            
        if assign == "yes":
            try:
                pass
            except:
                pass
            
        return str(ticketId),result,contactReault
    
    def sendMail(users,subject,contents,ticketId):
        import smtplib
        from email.mime.text import MIMEText
        
        des = "\n\nThis email auto send by Mozat Angel, if any questions, please kindly feed back to operation team. thanks !\nBest Regards\nMozat Angel"
        
        sender = 'wumingyou@mozat.com'
        receivers = map(lambda x:x.email,users)
        usersname = map(lambda x:x.name,users)
        if ticketId == None:
            ticketId = ""
        msg = MIMEText("Dear, "+", ".join(usersname)+"\n\n"+contents+"ticketId: "+ticketId+des)
        msg['Subject'] = "Angel "+subject+" error happened !"
        msg['From'] = "Mozat Angel"
        msg['To'] = "; ".join(receivers)
        try:
            s = smtplib.SMTP('i-smtp.mozat.com')
            s.sendmail(sender, receivers, msg.as_string())
            s.close()
            result = ""
            contactReault = "suc"
        except Exception, e:
            result = str(e)
            contactReault = "fail"
        return result,contactReault
    
    def sendSMS(users,subject,contents):
        import urllib2
        
        result = "suc"
        for user in users:
            try:
                smsUrl = settings.SMS_API % (str(user.phone), str(subject)+" error happened ! " +str(contents))
                smsResult = urllib2.urlopen(smsUrl.replace(" ","%20")).read()
                if smsResult != "{ret:0}":result = "fail"
            except:
                result = "fail"
        
        return result
    
    def rrdAlarm(widget,rrdTime):
        import rrdtool
        rrd_path = widget.rrd.path()
        info = rrdtool.info(rrd_path)
        last_update = info["last_update"]
        result = ""
        alarmError = False
        if time.time() - last_update > rrdTime*60:
            alarmError = True
            lastedTime = "from " + time.strftime("%m-%d %H:%M",time.localtime(int(last_update)))+" to "+time.strftime("%m-%d %H:%M",time.localtime())
            result = lastedTime +", \n" + widget.title + " no update sustained "+str(int(time.time() - last_update)/60)+" minutes !\n"
        elif widget.data_def:
            data_rrds = rrdtool.fetch(rrd_path, "-s", str(int(last_update)-int(rrdTime) * 60), "-e", str(last_update) + "-1", "LAST")
            try:
                data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
                data = list(data_rrds[2][0])
                ds = data_rrds[1]
                errorRrdValue = ""
                errorValues = ""
                for i in range(0, len(ds)):
                    if data_def.has_key(ds[i]):
                        field_def = data_def[ds[i]]
                        try:
                            ls_data = [ str(x[i]) for x in data_rrds[2] if x[i] != None ]
                            if False not in [eval( x + field_def[2]) for x in ls_data] and len(ls_data) > 0:
                                alarmError = True
                                errorRrdValue += ds[i]+","
                                if len(data_rrds[2])<=10:
                                    data_rrd = ["None" if x[i] == None else str('%.2f' % x[i]) for x in data_rrds[2]]
                                else:
                                    data_rrd = ["None" if x[i] == None else str('%.2f' % x[i]) for x in data_rrds[2]][-10:]
                                errorValues += "Lastest " + ds[i] + " values: " + ",".join(data_rrd)+"\n"
                        except:
                            pass
                    else:
                        pass
                lastedTime = "from " + time.strftime("%m-%d %H:%M",time.localtime(int(time.time())-rrdTime*60))+" to "+time.strftime("%m-%d %H:%M",time.localtime())
                result =  lastedTime +", \n"+widget.title+" " +errorRrdValue+" error sustained more than " + str(rrdTime)+ " minutes !\n"+errorValues
                
            except:
                return widget.data_def
        
        return alarmError,result
        
    def contrastLog(alarm,widget,alarmlog):
        rrdTime = 0
        alarmDataDef = eval(alarm.alarm_def.replace("\n", "").replace("\r", ""))
        
        if alarmlog == "":
            rrdTime = eval(alarmDataDef[1])["time"]
            alarmLevel = 1
            alarmMode = eval(alarmDataDef[1])["mode"]
            contactUsers = alarm.firstcontact.all()
        elif alarmlog.overdue == "2" or alarmDataDef.get(int(alarmlog.alarmlevel)+1,"") == "":
            if int(eval(alarmDataDef[int(alarmlog.alarmlevel)])["interval"])<(datetime.now()-alarmlog.created_on).seconds/60:
                rrdTime = eval(alarmDataDef[1])["time"]
                alarmLevel = 1
                alarmMode = eval(alarmDataDef[1])["mode"]
                contactUsers = alarm.firstcontact.all()
        elif (datetime.now()-alarmlog.created_on).seconds/60 > int(eval(alarmDataDef[int(alarmlog.alarmlevel)+1])["time"]):
            rrdTime = eval(alarmDataDef[int(alarmlog.alarmlevel)+1])["time"]
            alarmLevel = int(alarmlog.alarmlevel)+1
            alarmMode = eval(alarmDataDef[int(alarmlog.alarmlevel)+1])["mode"]
            contactUsers = eval("alarm."+contact_users[int(alarmlog.alarmlevel)+1]).all()
        if int(rrdTime) !=0:
            alarmError,result = rrdAlarm(widget,int(rrdTime))
            if alarmError == False:
                try:
                    alarmlog.overdue = "2"
                    alarmlog.save()
                except:
                    pass
                if alarmLevel!=1 and int(eval(alarmDataDef[int(alarmlog.alarmlevel)])["interval"])<(datetime.now()-alarmlog.created_on).seconds/60:
                    rrdTime = eval(alarmDataDef[1])["time"]
                    alarmLevel = 1
                    alarmMode = eval(alarmDataDef[1])["mode"]
                    contactUsers = alarm.firstcontact.all()
                    alarmError,result = rrdAlarm(widget,int(rrdTime))
            
            if alarmError:
                try:
                    if alarmlog.overdue == "2" or alarmDataDef.get(int(alarmlog.alarmlevel)+1,"") == "":
                        ticketId = ""
                    else:
                        ticketId = alarmlog.ticketid
                except:
                    ticketId = ""
                if "ticket" in alarmMode:
                    try:
                        assign = eval(alarmDataDef[i])["assign"]
                    except:
                        assign = "no"
                    ticketId,resultAlarm,contactReault = createTicket("[long_time]",widget,result,contactUsers,assign)
                if "email" in alarmMode:
                    resultAlarm,contactReault = sendMail(contactUsers,widget.title,result,ticketId)
                if "sms" in alarmMode:
                    contactReault = sendSMS(contactUsers,widget.title,"ticketID: "+str(ticketId))
                    resultAlarm = ""
                if "call" in alarmMode:
                    try:
                        contactReault = doCall()
                    except:
                        contactReault = "error"
                    resultAlarm = ""
                logs = AlarmLog()
                logs.title = alarm
                logs.widget = widget
                logs.alarmlevel = alarmLevel
                logs.alarmmode = alarmMode
                logs.ticketid = ticketId
                logs.overdue = "1"
                logs.save()
                logs.alarmuser = contactUsers
                logs.save()
                logs.result = result+"\n\n"+resultAlarm
                logs.contact_result = contactReault
                logs.save()
    def frequentrrdAlarm(widget):
        import rrdtool
        rrd_path = widget.rrd.path()
        info = rrdtool.info(rrd_path)
        last_update = info["last_update"]
        alarmError = False
        if widget.data_def:
            data_rrds = rrdtool.fetch(rrd_path, "-s", str(int(last_update)-1), "-e", "s+0", "LAST")
            try:
                data_def = eval(widget.data_def.replace("\n", "").replace("\r", ""))
                if time.time() - last_update > int(data_def["interval"])*60:
                    alarmError = True
                else:
                    data = data_rrds[2][0]
                    ds = data_rrds[1]
                    errorRrdValue = ""
                    errorValues = ""
                    for i in range(0, len(ds)):
                        if data_def.has_key(ds[i]):
                            field_def = data_def[ds[i]]
                            try:
                                if eval(str(data[i])+field_def[2]) and data[i] != None:
                                    alarmError = True
                                    break
                            except:
                                pass
            except:
                return widget.data_def
        
        return alarmError
    
    def alarmFrequent(alarm,widget,frequentAlarmLog):
        def saveFrequentLog(log,alarmLevel,alarmMode,ticketId,contactReault,result,contactUsers):
            log.alarmlevel = alarmLevel
            log.alarmmode = alarmMode
            log.ticketid = ticketId
            log.contact_result = contactReault
            log.result = result
            log.lasterror_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            log.alarmuser = contactUsers
            log.save()
            return log
            
        def doReport(alarmLevel,frequentAlarmLog,contactUsers):
            alarmMode = eval(alarmDataDef[alarmLevel])["mode"]
            result = widget.title + " error happened "+str(error_num_now)+" times !"
            ticketId = ""
            if "ticket" in str(alarmMode):
                try:
                    assign = eval(alarmDataDef[alarmLevel])["assign"]
                except:
                    assign = "no"
                ticketId,resultAlarm,contactReault = createTicket("[frequent]",widget,result,contactUsers,assign)
                frequentAlarmLog = saveFrequentLog(frequentAlarmLog,alarmLevel,alarmMode,ticketId,contactReault,result,contactUsers)
            if "email" in str(alarmMode):
                resultAlarm,contactReault = sendMail(contactUsers,widget.title,result,frequentAlarmLog.ticketid)
                frequentAlarmLog = saveFrequentLog(frequentAlarmLog,alarmLevel,alarmMode,str(frequentAlarmLog.ticketid),contactReault,result,contactUsers)
            if "sms" in str(alarmMode):
                contactReault = sendSMS(contactUsers,widget.title,"total error times: "+str(error_num_now))
                frequentAlarmLog = saveFrequentLog(frequentAlarmLog,alarmLevel,alarmMode,str(frequentAlarmLog.ticketid),contactReault,result,contactUsers)
            if "call" in alarmMode:
                try:
                    contactReault = doCall()
                except:
                    contactReault = "error"
                frequentAlarmLog = saveFrequentLog(frequentAlarmLog,alarmLevel,alarmMode,str(frequentAlarmLog.ticketid),contactReault,result,contactUsers)
        
        if frequentrrdAlarm(widget):
            if frequentAlarmLog != "":
                alarmlevel = frequentAlarmLog.alarmlevel
            else:
                alarmlevel = None
            if frequentAlarmLog == "" or frequentAlarmLog.lasterror == "False":
                log = FrequentAlarmLog()
                log.title = alarm
                log.widget = widget
                log.alarmlevel = alarmlevel
                log.lasterror = "True"
                log.error_num = 1
                log.save()
                frequentAlarmLog = FrequentAlarmLog.objects.filter(widget = widget.id).filter(created_on__gte = time.strftime("%Y-%m-%d",time.localtime())).order_by("-created_on")[0]

        elif frequentAlarmLog != "" and  frequentAlarmLog.lasterror == "True":
            frequentAlarmLog.lasterror = "False"
            frequentAlarmLog.save()
            
        alarmDataDef = eval(alarm.alarm_def.replace("\n", "").replace("\r", ""))
        alarmDataDefKeys = alarmDataDef.keys()
        alarmDataDefKeys.reverse()
        
        if frequentAlarmLog != "":
            for i in alarmDataDefKeys:
                alarmTime = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time() - int(eval(alarmDataDef[i])["alarm_time"])*60))
                error_num_now = FrequentAlarmLog.objects.filter(widget = widget.id).filter(created_on__gte = alarmTime).count()
                if error_num_now >= int(eval(alarmDataDef[i])["alarm_num"]):
                    if frequentAlarmLog.alarmlevel != int(i):
                        doReport(i,frequentAlarmLog,eval("alarm."+contact_users[i]).all())
                        break
                    elif frequentAlarmLog.alarmlevel == int(i):
                        try:
                            goingNo = True
                            alarmTime = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time() - int(eval(alarmDataDef[frequentAlarmLog.alarmlevel])["interval"])*60))
                            lastErrorLog = FrequentAlarmLog.objects.filter(widget = widget.id).filter(lasterror_time__gte = alarmTime).order_by("-lasterror_time")[0]
                            if time.time() - time.mktime(lastErrorLog.lasterror_time.timetuple()) < int(eval(alarmDataDef[frequentAlarmLog.alarmlevel])["alarm_time"])*60 :
                                goingNo = False
                        except:
                            goingNo = True
                        
                        if goingNo:
                            doReport(i,frequentAlarmLog,eval("alarm."+contact_users[i]).all())
                            break
    
    for alarm in Alarm.objects.all():
        if eval(alarm.enable):
            for widget in alarm.widget.filter(project__in = Project.objects.filter(alarm = "True")):
                try:
                    alarmlog = AlarmLog.objects.filter(widget = widget.id, title = alarm).order_by("-created_on")[0]
                except:
                    alarmlog = ""
                try:
                    contrastLog(alarm,widget,alarmlog)
                except:
                    pass
    
    for alarm in FrequentAlarm.objects.all():
        if eval(alarm.enable):
            for widget in alarm.widget.filter(project__in = Project.objects.filter(alarm = "True")):
                try:
                    frequentAlarmLog = FrequentAlarmLog.objects.filter(widget = widget.id,title = alarm).filter(created_on__gte = time.strftime("%Y-%m-%d",time.localtime())).order_by("-created_on")[0]
                except:
                    frequentAlarmLog = ""
                try:
                    alarmFrequent(alarm,widget,frequentAlarmLog)
                except:
                    pass

    alarmlogs = AlarmLog.objects.filter(created_on__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-24*3600))).order_by("widget","-created_on")
    frequentAlarmLogs = FrequentAlarmLog.objects.filter(lasterror_time__gte = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time())-24*3600))).order_by("widget","-lasterror_time")
    
    c = RequestContext(request,
        {"alarmlogs":alarmlogs,
        "frequentAlarmLogs":frequentAlarmLogs,
        })
    return render_to_response('servers/auto_alarm.html',c)

@login_required()
def alarm_test(request):
    import urllib2
    import datetime
    data = '''<br><br>
        <form action="">
        <input type="submit" name="test" value="Test Alarm">
        <input type="submit" name="stop" value="Stop Alarm">
        </form><br>
        Test result:<hr>%s
    '''
    if request.GET.has_key("test"):
        try:
            if doCall():
                result = "ok"
            else:
                result = "error"
        except Exception, e:
            result = str(e)
        log = AlarmTest()
        log.user = request.user
        log.result = result
        log.created_on = datetime.datetime.now()
        log.save()
    elif request.GET.has_key("stop"):
        try:
            result = "stop ok"
            smsUrl = settings.SMS_API % (settings.RING_PHONE_NUMBER, "%E6%92%A4%E9%98%B2")
            smsResult = urllib2.urlopen(smsUrl.replace(" ","%20")).read()
            if smsResult != "{ret:0}":result = "stop fail"
        except Exception, e:
            result = str(e.reason)
    else:
        result = """Alarm Page<hr>
        <iframe src="/alarm" width="100%" height="100%" frameborder="0"></iframe>
        """
    return HttpResponse(data % result)

def backuplog(request):
    import os
    from tail import tail
    result = []
    logpath = settings.LOGPATH
    files = os.listdir(logpath)
    timeNow = datetime.now()
    logName = request.GET.get("logname",False)
    mydate = request.GET.get("date",time.strftime("%Y-%m-%d"))
    if logName:
        try:
            try:
                log = BackupLog.objects.get(log_name=logName)
            except:
                log = BackupLog()
            log.name = request.GET["p"]
            log.email = request.GET["e"]
            log.log_type = request.GET["t"]
            log.log_name = logName
            log.save()
            remarks = log.remark.filter(created_on=mydate)
            if remarks.count() == 0:
                remark = BackupLogRemark(content = request.GET["r"])
                remark.save()
                log.remark.add(remark)
            else:
                remark = remarks[0]
                remark.content = request.GET["r"]
                remark.save()
        except:
            pass
        return HttpResponseRedirect("/backuplog/showinfo/")
    for i in files:
        try:
            lsi=[]
            try:
                data = ""
                f = open(logpath+i).readlines()
                for l in range(1,len(f)):
                    if f[-l][:15].startswith(mydate):
                        data = f[-l]
                        break
                data = data.replace("(","\\(").replace(")","\\)").replace("\.","\\.").split("^")
                if data == [""]:raise
            except:
                data = tail(logpath+i,2)[-1].split("^")
            lsi.append(i)
            lastTime = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S")
            mytimes = timeNow- lastTime
            if int(mytimes.days) > 0:
                mytime = 1440 * int(mytimes.days) + mytimes.seconds/60
            else:
                mytime =  mytimes.seconds/60
            if mytime > int(data[1]) and mydate == time.strftime("%Y-%m-%d"):
                lsi.append(data[0]+"<div class='errornote'>No update</div>")
            else:
                lsi.append(data[0].replace("_"," "))
            if data[2] == "error":
                lsi.append("<div class='errornote'>error</div>")
            else:
                lsi.append(data[2])
            if len(data[3]) > 40:
                lsi.append(data[3].replace("nnn","")[:37]+"...")
            else:
                lsi.append(data[3].replace("nnn","")+"")
            try:
                data = BackupLog.objects.get(log_name=i)
                remarks = data.remark.filter(created_on=mydate)
                lsi.insert(0,data.email)
                lsi.insert(0,data.name)
                lsi.insert(0,data.log_type)
                if remarks.count() != 0:
                    lsi.append(remarks[0].content)
                else:
                    lsi.append("")
            except:
                lsi.insert(0,"")
                lsi.insert(0,"")
                lsi.insert(0,"")
                lsi.append("")
            result.append(lsi)
        except:
            pass
            result.append(['','','',i+"<div class='errornote'>log format error</div>",''])
        result.sort()
    c = RequestContext(request,
        {"result":result,
         "mydate":mydate,
        })
    return render_to_response('servers/backuplog.html',c)

def showdetail(request):
    import os
    from tail import tail
    logPath = settings.LOGPATH
    name = request.GET["name"]
    date = request.GET.get("d",False)
    data = []
    if date:
        for l in open(logPath+name).readlines():
            if l[:15].startswith(date):
                data.append(l)
    else:
        lines = request.GET["l"]
        data = tail(logPath+name,int(lines))
    if name.endswith(".end"):
        try:
            result = []
            f = "".join(data).replace("(","\\(").replace(")","\\)").replace("\.","\\.")
            i = f.index("ip")
            result.append(f[:i].replace("^"," ").replace("nnn","<br />"))
            result.append("<table>\n")
            for l in f[i:].split("nnn"): 
                x = "<tr><td>"+"</td><td>".join(l.split(","))+"</td></tr>\n"
                result.append(x)
            result.append("</table>\n")
            result = "".join(result)
        except:
            result = ""
    else:
        result = "<br />".join(data).replace("^"," ").replace("nnn","<br />")

    response = HttpResponse(result)
    response["content-type"] = "text/plain"
    return response

def backuplogemail(request):
    import os
    from tail import tail
    def sendmail(c,n,r,d):
        import smtplib
        from email.mime.text import MIMEText

        des = "\n\nThis email auto send by Mozat Angel, if any questions, please kindly feed back to operation team. thanks !\nBest Regards\nMozat Angel"
        sender = 'wumingyou@mozat.com'
        msg = MIMEText("Dear %s,\n\n%s backup log errors,pls visit bleow url for more details\n http://angel.morange.com/backuplog/showinfo/?date=%s%s"  % (n,c,d,des))
        msg['Subject'] = "Backup log error happen !"
        msg['From'] = "Mozat Angel"
        msg['To'] = r
        s = smtplib.SMTP('i-smtp.mozat.com')
        s.sendmail(sender, r, msg.as_string())
        s.close()
        
    logpath = settings.LOGPATH
    files = os.listdir(logpath)
    timeNow = datetime.now()
    mydate = time.strftime("%Y-%m-%d")
    result = {}
    for i in files:
        try:
            try:
                data = ""
                f = open(logpath+i).readlines()
                for l in range(1,len(f)):
                    if f[-l][:15].startswith(mydate):
                        data = f[-l]
                        break
                data = data.replace("(","\\(").replace(")","\\)").replace("\.","\\.").split("^")
                if data == [""]:raise
            except:
                data = tail(logpath+i,2)[-1].split("^")
            lastTime = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S")
            mytimes = timeNow- lastTime
            if int(mytimes.days) > 0:
                mytime = 1440 * int(mytimes.days) + mytimes.seconds/60
            else:
                mytime =  mytimes.seconds/60
            if mytime > int(data[1]) and mydate == time.strftime("%Y-%m-%d") or data[2] == "error":
                try:
                    b = BackupLog.objects.get(log_name=i)
                    if b.mail.filter(name=i,log_date=data[0]).count() > 0:
                        continue
                except:
                    continue
                if result.has_key(b.name):
                    result[b.name].append((i,data[0]))
                else:
                    result[b.name] = [b.email,(i,data[0])]
        except:
            pass
    for i in result.keys():
        try:
            sendmail(",".join([x[0] for x in result[i][1:]]),i,result[i][0],mydate)
            for x,y in result[i][1:]:
                b = BackupLog.objects.get(log_name=x)
                m = BackupLogMail(name=x,log_date=y)
                m.save()
                b.mail.add(m)
        except:
            pass
    return HttpResponse("done")

@login_required()
def add_widget(request):
    import urllib2
    if request.GET.has_key("sync"):
        try:
            urllib2.urlopen("http://angel.morange.com/cmdb/updateservices")
            return HttpResponseRedirect("/cmdb/add")
        except:
            pass
    try:
        title = request.GET["t"]
        if title == "":raise
        serverId = request.GET["s"]
        project = request.GET["p"]
        w = Widget()
        w.title = title
        w.rrd = Rrd.objects.get(id=1026)
        w.server = Server.objects.get(id=serverId)
        w.category=WidgetCategory.objects.get(id=35)
        w.grade=WidgetGrade.objects.get(id=3)
        w.widget_type="1"
        w.service_type=WidgetServiceType.objects.get(id=request.GET["st"])
        w.graph_def='DEF:online={rrd}:online:LAST\nLINE:online#ff8882:Online'
        w.save()
        w.dashboard.add(27)
        w.project.add(project)
        
        return HttpResponseRedirect("/cmdb/add")
    except:
        pass
    servers = Server.objects.all().values("id","name","ip").order_by("ip")
    projects = Project.objects.all().values("id","name").order_by("name")
    widgets = Widget.objects.filter(created_on__gte="2012-11-23 00:00:00").order_by("-id")[:30]
    serviceType = WidgetServiceType.objects.all().order_by("name")
    
    return render_to_response("servers/add_widget.html",{"request":request,"servers":servers,"projects":projects,"widgets":widgets,"serviceType":serviceType})

def api_idc(request):
    import json
    ls = [];sf = {1:'Monet',2:'APP',3:'DB',4:'VMware'}
    servers = Server.objects.all()
    for s in servers:
        dt = {"ip":s.ip,"name":s.name,"function":sf[s.server_function],"project":s.project.name}
        ls.append(dt)
    
    return HttpResponse(json.dumps(ls, ensure_ascii=False))
     
def sync_server(request):
    import urllib2
    import json
    try:
        data = urllib2.urlopen(settings.IDC_API).read()
    except:
        return HttpResponse("api return error!")
        data = []
    
    servers = Server.objects.filter(idc__name="M1")
    data = json.loads(data)
    for d in data:
        if d['os_name'] == None:server_type="L"
        elif "Windows" in d['os_name']:server_type="W"
        elif "VMware" in d['os_name']:server_type="V"
        else:server_type="L"
        hard_disk = d['disk_gb']
        if hard_disk > 1024:hard_disk = "%.1fT" % (hard_disk/1024.0)
        else:hard_disk = "%dG" % hard_disk
        if d['ram_gb'] == None:ram = ""
        else:ram = "%dG" % d['ram_gb']
        state = "N"
        if d['state'] == "On":state = "Y"
        physical_server = "Y"
        if d['type'] == "virtual":physical_server = "N"
        if d['hostname'] == None:d['hostname'] = ""
        if d['ip'] == None:continue
        if d['host_ip'] == None:d['host_ip'] = ""
        d['hostname'] = d['hostname'].split(".")[0]
        try:
            s = servers.get(uid=d["uid"])
            s.ip=d['ip']
            s.name=d['hostname']
            s.physical_server_ip=d['host_ip']
            s.uid=d['uid']
            s.rack=d['rack']
            s.core=int(d['cpu_threads'])
            s.ram=ram
            s.hard_disk=hard_disk
            s.server_type=server_type
            s.physical_server=physical_server
            s.power_on=state
            s.label=d['label']
            s.save()
        except:
            s = Server(ip=d['ip'],name=d['hostname'],physical_server_ip=d['host_ip'],uid=d['uid'],rack=d['rack'],core=int(d['cpu_threads']),ram=ram,\
            hard_disk=hard_disk,physical_server=physical_server,server_type=server_type,power_on=state,label=d['label'],project_id=10,idc_id=1)
            s.save()
    return HttpResponse("done")

def widget_value(request):
    import rrdtool 
    import json
    widget = get_object_or_404(Widget,title=request.GET["widget"])
    result = {}
    d = int(time.time())
    t = d % 60
    d = d - t
    data = rrdtool.fetch(widget.rrd.path(), "-s", str(d-1), "-e", "s+0", "LAST")
    
    for x,y in zip(data[1],data[2][0]):
        result[x] = y
    
    return HttpResponse(json.dumps(result, ensure_ascii=False))
