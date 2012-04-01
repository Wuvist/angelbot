from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from servers.models import Server as s_server
from servers.models import Widget as s_service
from servers.models import IDC as s_idc
from servers.models import Project as s_project
from cmdb.models import *
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from datetime import datetime
import time


def syncdbservers(request):
    
    cmdbServers = Server.objects.all()
    serversLs = cmdbServers.values_list("server_id", flat=True)
    serversServers = s_server.objects.all()
    server_s = serversServers.values_list("id", flat=True)
    serversDel = list(set(serversLs)-set(server_s))
    cmdbServers.filter(id__in = serversDel).update(available="N",del_time = datetime.now())
    for s in serversServers:
        if s.id in serversLs:
            Server.objects.filter(server_id=s.id).update(ip = s.ip,server_id = s.id,name = s.name,password = s.password,\
            project = s.project.name,physical_server = s.physical_server,physical_server_ip = s.physical_server_ip,core = s.core,\
            ram = s.ram,hard_disk = s.hard_disk,server_function = s.server_function,server_type = s.server_type,\
            idc = s.idc.name,remark = s.remark,available = "Y",created_on = s.created_on)
        else:
            ser = Server()
            ser.ip = s.ip
            ser.server_id = s.id
            ser.name = s.name
            ser.password = s.password
            ser.project = s.project.name
            ser.physical_server = s.physical_server
            ser.physical_server_ip = s.physical_server_ip
            ser.core = s.core
            ser.ram = s.ram
            ser.hard_disk = s.hard_disk
            ser.server_function = s.server_function
            ser.server_type = s.server_type
            ser.idc = s.name
            ser.remark = s.remark
            ser.available = "Y"
            ser.created_on = s.created_on
            ser.save()
            
    if LastUpdate.objects.filter(title = "cmdbServerLastUpdate").count() == 0:
        LastUpdate(title = "cmdbServerLastUpdate", created_on = datetime.now()).save()
    else:
        LastUpdate.objects.filter(title = "cmdbServerLastUpdate").update(created_on = datetime.now())
        
    return HttpResponseRedirect('/cmdb/servers/')

@login_required
def show_servers(request):
    
    if not request.user.is_staff:
        raise Http404
    ip = request.GET.get("ip","")
    name = request.GET.get("name","")
    idc = request.GET.get("idc","")
    project = request.GET.get("project","")
    ispserver = request.GET.get("ispserver","")
    pip = request.GET.get("pip","")
    system = request.GET.get("system","")
    funtion = request.GET.get("funtion","")
    created_on = request.GET.get("created_on","")
    servers = Server.objects.filter(available = "Y", ip__contains=ip, name__contains=name, idc__contains=idc, \
    project__contains=project,physical_server__contains=ispserver, physical_server_ip__contains=pip, \
    server_type__contains=system, server_function__contains=funtion).order_by("ip")
    if created_on != "":
        servers = servers.filter(created_on__range=(time.strftime("%Y-%m-%d",time.strptime(created_on, "%Y-%m-%d")),\
        time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(created_on+" 23:59:59", "%Y-%m-%d %H:%M:%S"))))
        
    c = RequestContext(request, 
        {"servers":servers,
        "project":project,
        "projects":s_project.objects.all(),
        "lastUpdate":LastUpdate.objects.get(title = "cmdbServerLastUpdate"),
        "ip":ip,
        "name":name,
        "idc":idc,
        "idcs":s_idc.objects.all(),
        "ispserver":ispserver,
        "pip":pip,
        "system":system,
        "funtion":funtion,
        "created_on":created_on,
        })
    
    return render_to_response('cmdb/show_servers.html',c)

def syncdbservices(request):
    cmdbServices = Service.objects.all()
    servicesLs = cmdbServices.values_list("service_id", flat=True)
    serversServices = s_service.objects.all()
    services_s = serversServices.values_list("id", flat=True)
    servicesDel = list(set(servicesLs)-set(services_s))
    cmdbServices.filter(id__in = servicesDel).update(available="N",del_time = datetime.now())
    for s in serversServices:
        if s.server == None:
            server_id = ""
            system = ""
            ip = ""
            pip = ""
        else:
            ip=s.server.ip
            pip=s.server.physical_server_ip
            server_id = s.server.id
            system = s.server.server_type
        if s.id in servicesLs:
            Service.objects.filter(service_id=s.id).update(title = s.title,service_id=s.id,\
            project = ",".join([str(v) for v in s.project.all().values_list("name",flat=True)]),\
            dashboard = ",".join([str(v) for v in s.dashboard.all().values_list("id",flat=True)]),\
            physical_server_ip = pip, ip = ip,system = system,service_name = s.service_type.name,\
            service_type = s.service_type.type.name,path = s.path,remark = s.remark,available = "Y",created_on = s.created_on)
        else:
            ser = Service()
            ser.title = s.title
            ser.service_id = s.id
            ser.project = ",".join([str(v) for v in s.project.all().values_list("name",flat=True)])
            ser.dashboard = ",".join([str(v) for v in s.dashboard.all().values_list("id",flat=True)])
            ser.ip = ip
            ser.physical_server_ip = pip
            ser.server_id = server_id
            ser.system = system
            ser.service_name = s.service_type.name
            ser.service_type = s.service_type.type.name
            ser.path = s.path
            ser.remark = s.remark
            ser.available = "Y"
            ser.created_on = s.created_on
            ser.save()
    
    if LastUpdate.objects.filter(title = "cmdbServiceLastUpdate").count() == 0:
        LastUpdate(title = "cmdbServiceLastUpdate", created_on = datetime.now()).save()
    else:
        LastUpdate.objects.filter(title = "cmdbServiceLastUpdate").update(created_on = datetime.now())
        
    return HttpResponseRedirect('/cmdb/services/')


@login_required
def show_services(request):
    
    if not request.user.is_staff:
        raise Http404    
    ip = request.GET.get("ip","")
    title = request.GET.get("title","")
    service_name = request.GET.get("service_name","")
    service_type = request.GET.get("service_type","")
    project = request.GET.get("project","")
    service_type = request.GET.get("service_type","")
    pip = request.GET.get("pip","")
    system = request.GET.get("system","")
    remark = request.GET.get("remark","")
    created_on = request.GET.get("created_on","")
    services = Service.objects.filter(available = "Y", ip__contains=ip, title__contains=title, project__contains=project,\
    system__contains=system, physical_server_ip__contains=pip,\
    service_name__contains=service_name, service_type__contains=service_type, remark__contains=remark\
    ).order_by("title")
    if created_on != "":
        services = services.filter(created_on__range=(time.strftime("%Y-%m-%d",time.strptime(created_on, "%Y-%m-%d")),\
        time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(created_on+" 23:59:59", "%Y-%m-%d %H:%M:%S"))))
        
    c = RequestContext(request,
        {"services":services,
        "lastUpdate":LastUpdate.objects.get(title = "cmdbServiceLastUpdate"),
        "ip":ip,
        "title":title,
        "pip":pip,
        "service_name":service_name,
        "services_name":Service.objects.values_list("service_name",flat=True).annotate(),
        "service_type":service_name,
        "services_type":Service.objects.values_list("service_type",flat=True).annotate(),
        "project":project,
        "projects":Server.objects.values("project").annotate(),
        "system":system,
        "created_on":created_on,
        })
    
    return render_to_response('cmdb/show_services.html',c)

