from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from servers.models import Server
from servers.models import Widget
from servers.models import IDC as s_idc
from servers.models import Project as s_project
from servers.models import RemarkLog
from servers.models import ExtraLog
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from datetime import datetime
import time


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
    servers = Server.objects.filter(ip__contains=ip,name__icontains=name,idc__name__icontains=idc,physical_server__icontains=ispserver,physical_server_ip__icontains=pip,\
    server_type__icontains=system).order_by("ip")
    if funtion !="":
        servers = server.filter(server_function=funtion)
    if project != "":
        servers = servers.filter(project__contains=project)
    if created_on != "":
        servers = servers.filter(created_on__range=(time.strftime("%Y-%m-%d",time.strptime(created_on, "%Y-%m-%d")),\
        time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(created_on+" 23:59:59", "%Y-%m-%d %H:%M:%S"))))
    c = RequestContext(request,
        {"servers":servers,
        "project":project,
        "projects":s_project.objects.all().order_by("name"),
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
    
    services = Widget.objects.filter(server__ip__contains=ip, title__icontains=title,\
    server__server_type__contains=system, server__physical_server_ip__contains=pip,remark__contains=remark,).order_by("title")
    if service_name != "":
        services = services.filter(service_type__name=service_name)
    if service_type != "":
        services = services.filter(service_type__type__name=service_type)
    if project != "":
        services = services.filter(project__name=project)
    if created_on != "":
        services = services.filter(created_on__range=(time.strftime("%Y-%m-%d",time.strptime(created_on, "%Y-%m-%d")),\
        time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(created_on+" 23:59:59", "%Y-%m-%d %H:%M:%S"))))
        
        
    c = RequestContext(request,
        {"services":services,
        "ip":ip,
        "title":title,
        "pip":pip,
        "service_name":service_name,
        "services_name":Widget.objects.values_list("service_type__name",flat=True).annotate().order_by("service_type__name"),
        "service_type":service_type,
        "services_type":Widget.objects.values_list("service_type__type__name",flat=True).annotate().order_by("service_type__type__name"),
        "project":project,
        "projects":s_project.objects.values("name").annotate().order_by("name"),
        "projects_d":s_project.objects.all().exclude(server=None).values_list("name",flat=True).annotate().order_by("-sequence"),
        "system":system,
        "created_on":created_on,
        })
    
    return render_to_response('cmdb/show_services.html',c)

def cmdbDeployment(request):
    from cStringIO import StringIO
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    import json
    import datetime
    import re
    
    myTime = datetime.date.today() + datetime.timedelta(-1)
    def filterWidget(w):
        if w.service_type == None:
            w.dep_type = "---"
            w.dep_type_color = "white"
        else:
	    w.dep_type = w.service_type.type.name
	    w.dep_type_color = str(w.service_type.type.color)
        return w
            
    
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
                t = c.beginText(x+w/2-40,y+2.5*h/3)
                t.textLines(rectStr.split(";"))
                c.drawText(t)
            else:
                c.setFillColor("black")
                c.setFont("Helvetica", 7)
                t = c.beginText(x+10,y+2*h/3)
                t.textLines(rectStr.split("-"))
                c.drawText(t)
    
    def filterServer(s,c,x,y,w=100,h=8):
        def drawcpu_mem(s,c,v,x,y,w,h,yy,io=False,l=50):
            c.setFillColor("white")
            c.rect(x+w/2-20,y+yy,l,h,stroke=1,fill=1)
            if v != "x":
                c.setFillColor("black")
                c.setFont("Helvetica", 7)
                if io:c.drawCentredString(x+w/2-10+l,y+yy+2,"%.2f" % v)
                else:c.drawCentredString(x+w/2-10+l,y+yy+2,"%.2f" % v)
                #if io and s.server_type == "W":
                #    if v >= 1:v = 100
                #    else:v = v*100
                if v > 100:v = 100
                if v < 50:
                    c.setFillColor("lightgreen")
                    c.rect(x+w/2-20,y+yy,v/100.0*l,h,stroke=0,fill=1)
                elif 50 <= v < 70:
                    c.setFillColor("orange")
                    c.rect(x+w/2-20,y+yy,v/100.0*l,h,stroke=0,fill=1)
                    c.setFillColor("lightgreen")
                    c.rect(x+w/2-20,y+yy,0.499*l,h,stroke=0,fill=1)
                elif v >= 70:
                    c.setFillColor("red")
                    c.rect(x+w/2-20,y+yy,v/100.0*l,h,stroke=0,fill=1)
                    c.setFillColor("orange")
                    c.rect(x+w/2-20,y+yy,0.699*l,h,stroke=0,fill=1)
                    c.setFillColor("lightgreen")
                    c.rect(x+w/2-20,y+yy,0.499*l,h,stroke=0,fill=1)
                c.grid([x+w/2-20+i for i in range(0,l+10,10)],[y+yy,y+yy+h])
            return c
        dt = {"cpu":"x","mem":"x","io":"x"}
        try:
            perf = json.loads(s.perf)
            if perf["mem_pct_max2"] != None:dt["mem"]=float(perf["mem_pct_max2"])
            if perf["cpu_pct_max2"] != None:dt["cpu"]=float(perf["cpu_pct_max2"])
            if perf["disk_ms_max2"] != None:dt["io"]=float(perf["disk_ms_max2"])
        except:
            pass
        try:
            
            log = ExtraLog.objects.filter(mark=s.id,type=1,created_on=myTime).order_by("-id")[0]
            if log:dt["io"] = float(log.value)
        except:
            pass
        drawcpu_mem(s,c,dt["cpu"],x,y,w,h,22)
        drawcpu_mem(s,c,dt["mem"],x,y,w,h,12)
        drawcpu_mem(s,c,dt["io"],x,y,w,h,2,io=True)
        return s
    
    def main(maxX,maxY):
        c = canvas.Canvas(temp,(maxX+30,maxY))
        ylist = [];logo = 0
        for pro in projects:
            logo += 1;vm = True
            x=10;y=maxY-100;w=100;h=20;yserver = y - 2.5*h;xserver = x;xservice = x;maxXX = x;yls = [];colorDict = {}
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
                flag = False;serverColor = 'white'
                wx = len(servers.filter(physical_server_ip = s.physical_server_ip))
                if vm and s.server_function == 4:
                    vm = False
                    xserver = x
                    maxXX = x
                    if yls == []:
                        yserver -= 6 * h
                    else:
                        yserver = min(yls) - 3 * h
                        yls = []
                wserver = w
                if wx > 1:
                    wx -= 1
                    wserver = w*wx
                if wx*w + xserver > maxX - 10:
                    xserver = x
                    maxXX = wserver
                    if yls == []:
                        yserver -= 6 * h
                    else:
                        yserver = min(yls) - 3 * h
                        yls = []
                    if wx*w > maxX - 10:
                        n = (maxX - 10) / w + 1
                        flag = True
                
                if flag == True:wserver = w*n
                if s.idle == 'Y':serverColor = 'lightgreen'
                elif s.power_on == 'N':serverColor = 'lightgrey'
                drawRect(c,s.name.capitalize()+'('+s.ip[8:]+');'+str(s.rack).replace('None','')+' ['+str(s.core)+'-'+s.ram+'-'+s.hard_disk+'];cpu:;mem:;io :',serverColor,xserver,yserver,wserver,2.5*h)
                s = filterServer(s,c,xserver,yserver,wserver)
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
                        yservice = yserver - 2.5*h
                        drawRect(c,ss.name.capitalize()+'('+ss.ip[8:]+');['+str(ss.core)+'-'+ss.ram+'-'+ss.hard_disk+'];cpu:;mem:;io :','white',xxservice,yservice,w,2.5*h)
                        ss = filterServer(ss,c,xxservice,yservice,w)
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
                        yserver -= 6 * h
                    else:
                        yserver = min(yls) - 3 * h
                        yls = []
                    wserver = w*(wx-n)
                    if wx > n:
                        drawRect(c,'',"white",xserver,yserver,wserver,2.5*h)
                        c.drawCentredString(xserver+wserver/2,yserver+h*4/7,s.name.capitalize()+'('+s.ip[8:]+')')
                        c.drawCentredString(xserver+wserver/2,yserver+h*1/7,'['+str(s.core)+'-'+s.ram+'-'+s.hard_disk+']')
                    xxservice = x
                    for ss in serviceServers[n:]:
                        yservice = yserver - 2.5*h
                        if ss.idle == 'Y':serverColor = 'lightgreen'
                        elif ss.power_on == 'N':serverColor = 'lightgrey'
                        else:serverColor = 'white'
                        drawRect(c,ss.name.capitalize()+'('+ss.ip[8:]+');['+str(ss.core)+'-'+ss.ram+'-'+ss.hard_disk+'];cpu:;mem:;io :',serverColor,xxservice,yservice,w,2.5*h)
                        ss = filterServer(ss,c,xxservice,yservice,w)
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
                        yservice = yserver - 2.5*h
                        if ss.idle == 'Y':serverColor = 'lightgreen'
                        elif ss.power_on == 'N':serverColor = 'lightgrey'
                        else:serverColor = 'white'
                        drawRect(c,ss.name.capitalize()+'('+ss.ip[8:]+');['+str(ss.core)+'-'+ss.ram+'-'+ss.hard_disk+'];cpu:;mem:;io :',serverColor,xxservice,yservice,w,2.5*h)
                        ss = filterServer(ss,c,xxservice,yservice,w)
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
    services = Widget.objects.all()
    servers = Server.objects.all()
    servers_p = servers.filter(physical_server = "Y")
    projects =  request.GET.getlist("ps")    
    if len(projects) == 0:
        projects = s_project.objects.filter(server__in=servers_p).annotate().order_by("-sequence").values_list("name",flat=True)
    temp = StringIO()
    temp,yy = main(x,y)
    if yy < 0:
        temp.reset()
        temp,yy = main(x,-1*yy + y + 30)
    
    response = HttpResponse(temp.getvalue())
    response["conten-type"] = "application/pdf"
    response["Content-Disposition"] = ("attachment;filename=mozat_deployment_%s.pdf" % datetime.date.today())
    
    return response


