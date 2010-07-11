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
def rrd_img(request):
    from subprocess import Popen, PIPE
    rrd = request.GET["rrd"]
    width = request.GET["width"]
    height = request.GET["height"]
    cmd = 'rrdtool graph - -E --imgformat PNG --width %s --height %s DEF:myspeed=%s:stc:LAST:start=%d:end=%d LINE1:myspeed#FF0000' % (
        width, height, settings.RRD_PATH + rrd + ".rrd",1275609600, 1275696000)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
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