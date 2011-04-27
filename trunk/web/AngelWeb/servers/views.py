# Create your views here.
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from servers.models import *
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from datetime import datetime

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
def dashboard_show(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)
    if not request.user.is_superuser:
        try:
            dashboard.user.get(id = request.user.id)
        except ObjectDoesNotExist:
            raise Http404
    
    c = RequestContext(request, 
        {"dashboard":dashboard
        })
    return render_to_response('servers/show_dashboard.html',c)
    
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
    url = settings.BOT_URL + django_urlencode({"server": server.name, "cmd":cmd.text})
    result = fetch_page(url)
    log.result = result
    log.save()

    return HttpResponse(fetch_page(url))

def rrd_img(request, widget_id):
    widget = get_object_or_404(Widget, id=widget_id)
    from subprocess import Popen, PIPE
    width = request.GET["width"]
    height = request.GET["height"]
    start = request.GET["start"]
    end = request.GET["end"]
    check_lines = request.GET["cl"].replace('[','').replace(']','').replace('u\'','').replace('\'','').replace(' ','').split(',')
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

    def get_check_lines(line_diff,get_time):
        color = get_line(widget)[get_line(widget).index("LINE:"+line_diff)+5+len(line_diff):get_line(widget).index("LINE:"+line_diff)+len(line_diff)+12] #5+7
        line = "DEF:"+line_diff+"="+settings.RRD_PATH + widget.rrd.name + ".rrd:"+line_diff+":LAST LINE:"+line_diff+color+":"+line_diff.capitalize()
        if get_time == "1d":
            line += " " + "DEF:donline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+start+"-"+get_time+":end=start+1d SHIFT:donline:86400 LINE:donline#fbba5c:Yesterday"
        elif get_time == "1w":
            one_day = " " + "DEF:donline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+start+"-1d:end=start+1d SHIFT:donline:86400 LINE:donline#fbba5c:Yesterday"
            line += one_day + " " + "DEF:wonline="+settings.RRD_PATH+widget.rrd.name+".rrd:"+line_diff+":LAST:start="+start+"-"+get_time+":end=start+1d SHIFT:wonline:604800 LINE:wonline#b5b5b5:LastWeek"
        return line
    
    if check_lines[0] == "":
        line = get_line(widget)
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
def rrd_show_widget_graph(request, rrd_id, widget_id):
    import re
    import time
    lines = []
    check_lines = []
    rrd = get_object_or_404(Rrd, id=rrd_id)
    widget = get_object_or_404(Widget, id=widget_id)
    line = widget.graph_def.replace("{rrd}", settings.RRD_PATH + widget.rrd.name + ".rrd").replace('\n','')
    lines = re.compile( "LINE:*?(\w+).*?" ).findall(line)
    end = "s%2b1d"
    graph_option = ""
    
    if request.GET.has_key("date"):
        show_date = request.GET["date"]
    else:
        show_date = time.strftime("%Y-%m-%d")
        
    if request.GET.has_key("show1d"):
        graph_option += "&1d=1"

    if request.GET.has_key("show1w"):
        graph_option += "&1w=1&1d=1"
        
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
        "widget": widget,
        "show_date" : show_date,
        "start": start,
        "end": end,
        "graph_option":graph_option,
        "lines":lines,
        "check_lines":check_lines,
        "check_line_values": check_line_values,
        "checkall":checkall,
        })
    return render_to_response('servers/rrd_show_graph.html',c)

def parser(request,widget_id):
    import matplotlib
    matplotlib.use('Agg')
    import numpy as np
    import time
    import rrdtool
    from cStringIO import StringIO
    from matplotlib import pyplot as plt
    from subprocess import Popen, PIPE
    
    widget = get_object_or_404(Widget,id = widget_id)
    rrd_name = widget.rrd.name
    check_lines = request.GET["cl"].replace('[','').replace(']','').replace('u\'','').replace('\'','').replace(' ','').split(',')
    rrd_lines = rrdtool.fetch(widget.rrd.path(), "-s", str(2), "-e", "s+0", "LAST")[1]
    if check_lines == ['']:
        check_lines = rrd_lines
    start = int(time.mktime(datetime.strptime(request.GET["start"], "%Y-%m-%d^%H:%M:%S").timetuple()))
    end = int(time.mktime(datetime.strptime(request.GET["end"], "%Y-%m-%d^%H:%M:%S").timetuple()))
    if start == end:
        start -= 86400
    start -= 60
    cmd = "rrdtool fetch " + widget.rrd.path() + " LAST -s " + str(start) +" -e " + str(end)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    data_ls = [x.split(" ") for x in stdout.replace(":","").replace("  ","").replace("n","-").replace("N","-").replace("\r","\n").split("\n") ]
    
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
    
    def start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x):
        list_all = []
        times_ls = []
        for i in range(0,len(rrd_lines)):
            if rrd_lines[i] in check_lines:
                list_all.append(parser_time(data_ls, i+1, start_time_number))
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
        list_all.append(times_ls)
        return list_all
    
    def parser_week(rrd_lines,check_lines,data_ls):
        def avaerge_week(data_ls,line_number):
            result = []
            total = 0
            j = 10080
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
        
        def start_week(rrd_lines,check_lines,data_ls,):
            list_all = []
            times_ls = []
            for i in range(0,len(rrd_lines)):
                if rrd_lines[i] in check_lines:
                    list_all.append(avaerge_week(data_ls, i+1))
            j = 10080
            data_ls_count = len(data_ls)
            for i in range(data_ls_count):
                try:
                    if i == data_ls_count - 2:
                        times_ls.append(time.strftime("%Y-%m-%d",time.localtime(int(data_ls[i][0])-60)))
                    elif i == j:
                        times_ls.append(time.strftime("%Y-%m-%d",time.localtime(int(data_ls[i][0]))))
                        j += 10080                     
                except:
                    pass
            list_all.append(times_ls)
            
            return list_all
        return start_week(rrd_lines,check_lines,data_ls,)
    
    if request.GET["ptime"] =="hour":
        start_time_number = 10
        p_last_time = 'time.strftime("%m-%d %H:%M",time.localtime(int(i[0])-60))[:-2]+"00"'
        time_x = 'time.strftime("%m-%d %H:%M",time.localtime(int(i[0])-3600))'
        result = start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x)
    elif request.GET["ptime"] =="day":
        start_time_number = 8
        p_last_time = 'time.strftime("%Y-%m-%d",time.localtime(int(i[0])-60))'
        time_x = 'time.strftime("%Y-%m-%d",time.localtime(int(i[0])-86400))'
        result = start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x)
    elif request.GET["ptime"] == "week":
        result = parser_week(rrd_lines,check_lines,data_ls)
    else:
        # elif request.GET["ptime"] == "month":
        start_time_number = 6
        p_last_time = 'time.strftime("%Y-%m", time.localtime(int(i[0])-60))'
        time_x = 'time.strftime("%Y-%m",time.localtime(int(i[0])-2419200))'
        result = start(rrd_lines,check_lines,data_ls,start_time_number,p_last_time,time_x)

    x_values = []
    if len(result[-1]) >= 18:
        interval = len(result[-1])/9
        for i in range(0, len(result[-1]), interval):
            x_values.append(result[-1][i])
    else:
        x_values = result[-1]
        interval = 1

    fig = plt.figure(figsize=(20,9))
    for i in range(len(result)-1):
        plt.plot(result[i])
    
    plt.legend(check_lines, loc="upper right",shadow=True)
    plt.xticks(np.arange(0,len(result[-1]),interval),x_values)
    plt.title(request.GET["start"]+"_"+request.GET["end"]+"_"+widget.category+"-"+widget.title+"/"+request.GET["ptime"])
    plt.grid(True)
    fig.autofmt_xdate()
    pic_buf = StringIO()
    plt.savefig(pic_buf,dpi=65)
    image_data = pic_buf.getvalue()
    pic_buf.close()
    plt.close()
    
    response = HttpResponse(image_data)
    response["content-type"] = "image/png"
    return response
    
def show_parse_graph(request,widget_id):
    import re
    import time
    widget = get_object_or_404(Widget, id=widget_id)
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
        
    c = RequestContext(request,
        {"widget":widget,
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
        })
    return render_to_response('servers/rrd_parse.html',c)

