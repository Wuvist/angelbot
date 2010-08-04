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

    line = get_line(widget)
    if request.GET.has_key("1d"):
        line += " " + get_line_diff(widget, "1d")

    if request.GET.has_key("1w"):
        line += " " + get_line_diff(widget, "1w") 
        
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
    print
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
    rrd = get_object_or_404(Rrd, id=rrd_id)
    widget = get_object_or_404(Widget, id=widget_id)
    end = "s%2b1d"
    graph_option = ""
    import time
    if request.GET.has_key("date"):
        show_date = request.GET["date"]
    else:
        show_date = time.strftime("%Y-%m-%d")
        
    if request.GET.has_key("show1d"):
        graph_option += "&1d=1"

    if request.GET.has_key("show1w"):
        graph_option += "&1w=1&1d=1"
        
    start_time = show_date + ' 00:00'
    start_time = time.strptime(start_time, "%Y-%m-%d %H:%M")
    start_time = int(time.mktime(start_time))
    start = start_time
    
    c = RequestContext(request,
        {"rrd":rrd,
        "widget": widget,
        "show_date" : show_date,
        "start": start,
        "end": end,
        "graph_option":graph_option
        })
    return render_to_response('servers/rrd_show_graph.html',c)