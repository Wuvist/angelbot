from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from servers.models import Server as s_server
from servers.models import Widget as s_service
from servers.models import IDC as s_idc
from servers.models import Project as s_project
from servers.models import RemarkLog
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
    cmdbServers.filter(server_id__in = serversDel).update(available="N",del_time = datetime.now())
    for s in serversServers:
        if s.id in serversLs:
            Server.objects.filter(server_id=s.id).update(ip = s.ip,server_id = s.id,name = s.name,password = s.password,\
            project = s.project.name,physical_server = s.physical_server,physical_server_ip = s.physical_server_ip,core = s.core,\
            ram = s.ram,hard_disk = s.hard_disk,server_function = s.server_function,server_type = s.server_type,\
            idc = s.idc.name,power_on=s.power_on,remark = s.remark,available = "Y",created_on = s.created_on)
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
            ser.idc = s.idc.name
            ser.power_on = s.power_on
            ser.remark = s.remark
            ser.available = "Y"
            ser.created_on = s.created_on
            ser.save()
            
    if LastUpdate.objects.filter(title = "cmdbServerLastUpdate").count() == 0:
        LastUpdate(title = "cmdbServerLastUpdate", created_on = datetime.now()).save()
    else:
        LastUpdate.objects.filter(title = "cmdbServerLastUpdate").update(created_on = datetime.now())
        
    return HttpResponse('<script type="text/javascript">window.history.back();</script>')

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
    servers = Server.objects.filter(ip__contains=ip,name__icontains=name,idc__contains=idc,physical_server__contains=ispserver,\
    physical_server_ip__contains=pip,server_type__contains=system, server_function__contains=funtion,available = "Y").order_by("ip")
    if project != "":
        servers = servers.filter(project__contains=project)
    if created_on != "":
        servers = servers.filter(created_on__range=(time.strftime("%Y-%m-%d",time.strptime(created_on, "%Y-%m-%d")),\
        time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(created_on+" 23:59:59", "%Y-%m-%d %H:%M:%S"))))
        
    try:
        LastUpdateTime = LastUpdate.objects.get(title = "cmdbServerLastUpdate")
    except:
        LastUpdateTime = ""
    
    c = RequestContext(request,
        {"servers":servers,
        "project":project,
        "projects":s_project.objects.all().order_by("name"),
        "lastUpdate":LastUpdateTime,
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
    serversServices = s_service.objects.exclude(server = None)
    services_s = serversServices.values_list("id", flat=True)
    servicesDel = list(set(servicesLs)-set(services_s))
    cmdbServices.filter(service_id__in = servicesDel).update(available="N",del_time = datetime.now())
    for s in serversServices:
        ip=s.server.ip
        pip=s.server.physical_server_ip
        server_id = s.server.id
        system = s.server.server_type
        if s.service_type != None:
            service_name = s.service_type.name
            service_typeName = s.service_type.type.name
            color = s.service_type.type.color
        else:
            service_name = "---"
            service_typeName = "---"
            color = "white"
        projects = ",".join([str(v) for v in s.project.all().values_list("name",flat=True)])
        if projects == "":
            projects = "---"
        if s.id in servicesLs:
            Service.objects.filter(service_id=s.id).update(title = s.title,service_id=s.id,\
            project = projects,dashboard = ",".join([str(v) for v in s.dashboard.all().values_list("id",flat=True)]),\
            physical_server_ip = pip, ip = ip,system = system,service_name = service_name,color = color,\
            service_type = service_typeName,path = s.path,remark = s.remark,available = "Y",created_on = s.created_on)
        else:
            ser = Service()
            ser.title = s.title
            ser.service_id = s.id
            ser.project = projects
            ser.dashboard = ",".join([str(v) for v in s.dashboard.all().values_list("id",flat=True)])
            ser.ip = ip
            ser.physical_server_ip = pip
            ser.server_id = server_id
            ser.system = system
            ser.service_name = service_name
            ser.service_type = service_typeName
            ser.color = color
            ser.path = s.path
            ser.remark = s.remark
            ser.available = "Y"
            ser.created_on = s.created_on
            ser.save()
    
    if LastUpdate.objects.filter(title = "cmdbServiceLastUpdate").count() == 0:
        LastUpdate(title = "cmdbServiceLastUpdate", created_on = datetime.now()).save()
    else:
        LastUpdate.objects.filter(title = "cmdbServiceLastUpdate").update(created_on = datetime.now())
        
    return HttpResponse('<script type="text/javascript">window.history.back();</script>')


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
    
    services = Service.objects.filter(available = "Y", ip__contains=ip, title__icontains=title,\
    system__contains=system, physical_server_ip__contains=pip,remark__contains=remark,).order_by("title")
    if service_name != "":
        services = services.filter(service_name=service_name)
    if service_type != "":
        services = services.filter(service_type=service_type)
    if project != "":
        services = services.filter(project=project)
    if created_on != "":
        services = services.filter(created_on__range=(time.strftime("%Y-%m-%d",time.strptime(created_on, "%Y-%m-%d")),\
        time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(created_on+" 23:59:59", "%Y-%m-%d %H:%M:%S"))))
        
    try:
        LastUpdateTime = LastUpdate.objects.get(title = "cmdbServiceLastUpdate")
    except:
        LastUpdateTime = ""
        
    c = RequestContext(request,
        {"services":services,
        "lastUpdate":LastUpdateTime,
        "ip":ip,
        "title":title,
        "pip":pip,
        "service_name":service_name,
        "services_name":Service.objects.values_list("service_name",flat=True).annotate().order_by("service_name"),
        "service_type":service_type,
        "services_type":Service.objects.values_list("service_type",flat=True).annotate().order_by("service_type"),
        "project":project,
        "projects":Service.objects.values("project").annotate().order_by("project"),
        "projects_d":Server.objects.filter(available="Y",physical_server="Y").values_list("project",flat = True).annotate(),
        "system":system,
        "created_on":created_on,
        })
    
    return render_to_response('cmdb/show_services.html',c)

def cmdbDeployment(request):
    from cStringIO import StringIO
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    import json
    import time
    import re
    
    try:
        start_s = settings.DEPLOYMENT_CONSUMPTION_START
        end_s = settings.DEPLOYMENT_CONSUMPTION_END
    except:
        start_s = 3
        end_s = 6
    
    myTime = time.strftime("%Y-%m-%d")
    def filterWidget(w):
        if w.service_type == None:
            w.dep_type = "---"
            w.dep_type_color = "white"
        else:
	    w.dep_type = w.service_type.type.name
	    w.dep_type_color = str(w.service_type.type.color)
        return w
    def filterServer(s):
        try:
            dt = {"cpu":"x","mem":"x","io":[]}
            data = RemarkLog.objects.get(mark=s.id,type=1,label=str(start_s)+"_"+str(end_s),created_on=myTime)
            data = json.loads(data.value)
            for k in data.keys():
                if k == "load":dt["cpu"]="%.0f%%" % data["load"]
                elif k == "cpu":dt["cpu"]="%.0f%%" % data["cpu"]
                elif 'diskqueue' in k:dt["io"].append(data[k])
                elif k == "util":dt["io"].append(data[k])
                elif k == 'mem':dt["mem"]="%.0f%%" % (data['mem']*100)
            if dt["io"] == []:dt["io"] = "x"
            else:dt["io"] = "%.0f" % max(dt["io"])
            s.cpu_mem_io = dt
        except:
            s.cpu_mem_io = {"cpu":"x","mem":"x","io":"x"}
        return s
            
    
    def drawRect(c,rectStr,color,x,y,w,h):
        c.setStrokeColor("black")
        c.setFillColor(color)
        c.rect(x,y,w,h,stroke=1,fill=1)
        if len(rectStr) <= 15:
            c.setFillColor("black")
            c.setFont("Helvetica", 10)
            c.drawCentredString(x+w/2,y+h/3,rectStr)
        elif 15 < len(rectStr) < 20:
            c.setFillColor("black")
            c.setFont("Helvetica", 8)
            c.drawCentredString(x+w/2,y+h/3,rectStr)
        elif len(rectStr) >= 20:
            if '[' in rectStr and ']' in rectStr:
                c.setFillColor("black")
                c.setFont("Helvetica", 7)
                t = c.beginText(x+w/2-40,y+2*h/3)
                t.textLines(rectStr.split(";"))
                c.drawText(t)
            else:
                c.setFillColor("black")
                c.setFont("Helvetica", 7)
                t = c.beginText(x+10,y+2*h/3)
                t.textLines(rectStr.split("-"))
                c.drawText(t)
    
    def main(maxX,maxY):
        c = canvas.Canvas(temp,(maxX+30,maxY))
        ylist = [];logo = 0
        for pro in projects:
            logo += 1;vm = True
            x=10;y=maxY-100;w=100;h=20;yserver = y - 1.5*h;xserver = x;xservice = x;maxXX = x;yls = [];colorDict = {}
            pservers = servers_p.filter(project__name = pro).order_by("server_function")
            c.setFont("Helvetica", 10)
            c.drawCentredString(maxX/2,maxY-20,pro +" deployment")
            c.setStrokeColor("black")
            c.setFillColor("white")
            c.rect(maxX-250,maxY-35,160,15,stroke=1,fill=1)
            c.setFillColor("black")
            c.drawString(maxX-247,maxY-30,"Server(ip) Rock [cores-RAM-HD]")
            try:c.drawString(x+20,maxY-50,"IDC: " + pservers[0].idc.name)
            except:pass
            for s in pservers:
                s = filterServer(s)
                flag = False;serverColor = 'white'
                wx = len(servers.filter(physical_server_ip = s.physical_server_ip))
                if vm and s.server_function == 4:
                    vm = False
                    xserver = x
                    maxXX = x
                    if yls == []:
                        yserver -= 60
                    else:
                        yserver = min(yls) - 2*h
                        yls = []
                '''
                for n in range(wx):
                    n += 1
                    if w*n + xserver > maxX - 10:
                        if n == 1 and wx == 1:break
                        elif n == 1:n = 0
                        flag = True
                        break
                if n > 1:n -= 1
                wserver = w*n
                if n == 1 and wx != 1:wserver = w*(wx-1)
                maxXX += wserver #will start new line when last vm step across two lines
                if maxXX > maxX - 10 and flag != True and wx < 2:
                    xserver = x
                    maxXX = wserver
                    if yls == []:
                        yserver -= 60
                    else:
                        yserver = min(yls) - 2*h
                        yls = []'''
                wserver = w
                if wx > 1:
                    wx -= 1
                    wserver = w*wx
                if wx*w + xserver > maxX - 10:
                    xserver = x
                    maxXX = wserver
                    if yls == []:
                        yserver -= 60
                    else:
                        yserver = min(yls) - 2 * h
                        yls = []
                    if wx*w > maxX - 10:
                        n = (maxX - 10) / w + 1
                        flag = True
                
                if flag == True:wserver = w*n
                if s.idle == 'Y':serverColor = 'lightgreen'
                elif s.power_on == 'N':serverColor = 'lightgrey'
                #if n != 0:
                drawRect(c,s.name.capitalize()+'('+s.ip[8:]+');'+str(s.rack).replace('None','')+' ['+str(s.core)+'-'+s.ram+'-'+s.hard_disk+'];Usage ['+s.cpu_mem_io['cpu']+'-'+s.cpu_mem_io['mem']+'-'+s.cpu_mem_io['io']+']',serverColor,xserver,yserver,wserver,1.5*h)
                serviceServers = servers.filter(physical_server_ip = s.physical_server_ip).exclude(ip = s.physical_server_ip)
                if len(serviceServers) == 0:
                    yservicea = yserver
                    for ssss in services.filter(server = s).exclude(service_type__type__name__contains="IDC"):
                        ssss = filterWidget(ssss)
                        yservicea -= h
                        yls.append(yservicea)
                        drawRect(c,re.sub('\(\d+\.\d+\)','',ssss.title),ssss.dep_type_color,xserver,yservicea,w,h)
                        if ssss.service_type not in colorDict:
                            colorDict[ssss.dep_type] = ssss.dep_type_color
                elif flag:
                    xxservice = xserver
                    for ss in serviceServers[:n]:
                        ss = filterServer(ss)
                        yservice = yserver - 1.5*h
                        drawRect(c,ss.name.capitalize()+'('+ss.ip[8:]+');['+str(ss.core)+'-'+ss.ram+'-'+ss.hard_disk+'];Usage ['+ss.cpu_mem_io['cpu']+'-'+ss.cpu_mem_io['mem']+'-'+ss.cpu_mem_io['io']+']','white',xxservice,yservice,w,1.5*h)
                        for sss in services.filter(server = ss).exclude(service_type__type__name__contains="IDC"):
                            sss = filterWidget(sss)
                            wservices = w
                            yservice -= h
                            yls.append(yservice)
                            drawRect(c,re.sub('\(\d+\.\d+\)','',sss.title),sss.dep_type_color,xxservice,yservice,wservices,h)
                            if sss.service_type not in colorDict:
                                colorDict[sss.dep_type] = sss.dep_type_color
                        xxservice += w
                    xserver = x
                    if yls == []:
                        yserver -= 60
                    else:
                        yserver = min(yls) - 2*h
                        yls = []
                    wserver = w*(wx-n-1)
                    if wx -1 > n:
                        drawRect(c,'',"white",xserver,yserver,wserver,1.5*h)
                        c.drawCentredString(xserver+wserver/2,yserver+h*4/7,s.name.capitalize()+'('+s.ip[8:]+')')
                        c.drawCentredString(xserver+wserver/2,yserver+h*1/7,'['+str(s.core)+'-'+s.ram+'-'+s.hard_disk+']')
                    xxservice = x
                    for ss in serviceServers[n:]:
                        ss = filterServer(ss)
                        yservice = yserver - 1.5*h
                        if ss.idle == 'Y':serverColor = 'lightgreen'
                        elif ss.power_on == 'N':serverColor = 'lightgrey'
                        else:serverColor = 'white'
                        drawRect(c,ss.name.capitalize()+'('+ss.ip[8:]+');['+str(ss.core)+'-'+ss.ram+'-'+ss.hard_disk+'];Usage ['+ss.cpu_mem_io['cpu']+'-'+ss.cpu_mem_io['mem']+'-'+ss.cpu_mem_io['io']+']',serverColor,xxservice,yservice,w,1.5*h)
                        for sss in services.filter(server = ss).exclude(service_type__type__name__contains="IDC"):
                            sss = filterWidget(sss)
                            wservices = w
                            yservice -= h
                            yls.append(yservice)
                            drawRect(c,re.sub('\(\d+\.\d+\)','',sss.title),sss.dep_type_color,xxservice,yservice,wservices,h)
                            if sss.service_type not in colorDict:
                                colorDict[sss.dep_type] = sss.dep_type_color
                        xxservice += w
                else:
                    xxservice = xserver
                    for ss in serviceServers:
                        ss = filterServer(ss)
                        yservice = yserver - 1.5*h
                        if ss.idle == 'Y':serverColor = 'lightgreen'
                        elif ss.power_on == 'N':serverColor = 'lightgrey'
                        else:serverColor = 'white'
                        drawRect(c,ss.name.capitalize()+'('+ss.ip[8:]+');['+str(ss.core)+'-'+ss.ram+'-'+ss.hard_disk+'];Usage ['+ss.cpu_mem_io['cpu']+'-'+ss.cpu_mem_io['mem']+'-'+ss.cpu_mem_io['io']+']',serverColor,xxservice,yservice,w,1.5*h)
                        for sss in services.filter(server = ss).exclude(service_type__type__name__contains="IDC"):
                            sss = filterWidget(sss)
                            wservices = w
                            yservice -= h
                            yls.append(yservice)
                            drawRect(c,re.sub('\(.*\)','',sss.title),sss.dep_type_color,xxservice,yservice,wservices,h)
                            if sss.service_type not in colorDict:
                                colorDict[sss.dep_type] = sss.dep_type_color
                        xxservice += w
                xserver += wserver + 5
                if wx > 1 and xserver > 100:xserver += w
                ylist += yls

            xp = maxX-250;yp=maxY-50;wp=80;hp=15;z=4;i=0
            for d in colorDict.keys():
                i += 1
                if i > z:
                    z += 4
                    yp = maxY - 50
                    xp += wp
                drawRect(c,d,colorDict[d],xp,yp,wp,hp)
                yp -= hp
            if logo == len(projects):
                c.setFillColor("black")
                c.drawCentredString(maxX/2,5,'(c) Mozat Pte Ltd. All rights reserved.')
            c.showPage()    
        c.save()
        
        return temp,min(ylist)
    
    x = 1000;y = 500;
    services = s_service.objects.all()
    servers = s_server.objects.all()
    servers_p = servers.filter(physical_server = "Y")
    projects =  request.GET.getlist("ps")    
    if len(projects) == 0:
        projects = ["shabik360"]+list(servers_p.exclude(project__name="shabik360").values_list("project__name",flat = True).annotate())
    temp = StringIO()
    temp,yy = main(x,y)
    if yy < 0:
        temp.reset()
        temp,yy = main(x,-1*yy + y + 30)
    
    response = HttpResponse(temp.getvalue())
    response["conten-type"] = "application/pdf"
    response["Content-Disposition"] = ("attachment;filename=mozat_deployment_%s.pdf" % myTime)
    
    return response


