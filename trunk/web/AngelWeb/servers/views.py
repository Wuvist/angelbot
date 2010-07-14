# Create your views here.
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from servers.models import *
from django.conf import settings

@login_required()
def show(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    cmds = Cmd.objects.filter(server_type=server.server_type).all()
    c = RequestContext(request, 
        {"server":server,
        "cmds":cmds
        })
    return render_to_response('servers/show.html',c)
    
@login_required()
def dashboard_show(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)
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
    
    url = settings.BOT_URL + "server=" + server.name + "&cmd=" + cmd.text.replace(" ", "%20")

    return HttpResponse(fetch_page(url))



@login_required()
def rrd_img(request, widget_id):
    widget = get_object_or_404(Widget, id=widget_id)

    def get_line(widget):
        return widget.graph_def.replace("{rrd}", settings.RRD_PATH + widget.rrd.name + ".rrd").replace("\n", "").replace("\r", " ")
    from subprocess import Popen, PIPE
    width = request.GET["width"]
    height = request.GET["height"]
    start = request.GET["start"]
    end = request.GET["end"]
    cmd = 'rrdtool graph - -E --imgformat PNG -e %s -s %s --width %s --height %s %s' % (
        end, start, width, height, get_line(widget))
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
    cmd = 'rrdtool create %s %s' % (settings.RRD_PATH + rrd.name + ".rrd", rrd.setting.replace("\n", "").replace("\r", " "))
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return HttpResponseRedirect("/rrd/list")
    
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

    import time
    if request.GET.has_key("date"):
        show_date = request.GET["date"]
    else:
        show_date = time.strftime("%Y-%m-%d")
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
        })
    return render_to_response('servers/rrd_show_graph.html',c)