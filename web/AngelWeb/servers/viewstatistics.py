# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from servers.models import *
from django.conf import settings

def ticket_show(request,ticketID):
    ticket = get_object_or_404(Ticket,id = ticketID)
    users = User.objects.filter(is_staff=True).order_by("username")
    edit = False
    if request.user == ticket.recorder or request.user == ticket.assignto or request.user.id == 3 or ticket.assignto==None:
        edit = True
    
    if request.POST.has_key("addcomment") and request.POST["addcomment"] != "":
        action = TicketAction()
        action.user = request.user
        action.actiontype = "comment"
        action.action = request.POST["addcomment"]
        action.save()
        ticket.action.add(action)
        log = TicketHistory()
        log.user = request.user
        log.content = "add comment"
        log.save()
        ticket.history.add(log)
    elif request.POST.has_key("addaction"):
        his = "";assto = int(request.POST["assto"]);status = request.POST["status"]
        inctype = request.POST["inctype"];addaction =  request.POST["addaction"]
        if assto != ticket.assignto.id:
            his += "Assign to: "+ticket.assignto.username+" --->"+users.get(id=assto).username+"<br>\n"
            ticket.assignto = users.get(id=assto)
            ticket.save()
        if inctype != ticket.incidenttype:
            his += "Incident type: "+ticket.incidenttype+" --->"+inctype+"<br>\n"
            ticket.incidenttype = inctype
            ticket.save()
        if addaction != "":
            his += "Add action taken<br>\n"
            action = TicketAction()
            action.user = request.user
            action.actiontype = "action"
            action.action = request.POST["addaction"]
            action.save()
            ticket.action.add(action)
        if status != ticket.status:
            his += "Status: "+ticket.status+" --->"+status+"<br>\n"
            ticket.status = status
            ticket.incidenttype = inctype
            ticket.save()
        if his != "":
            log = TicketHistory()
            log.user = request.user
            log.content = his
            log.save()
            ticket.history.add(log)
            
    
    c = RequestContext(request,{
        "ticket":ticket,
        "edit":edit,
        "users":users,
        
    })
    return render_to_response("servers/ticket.html",c)



def statistics_update(request):
    import time
    import rrdtool
    import threading
    from subprocess import Popen, PIPE
    def operation(widget,startTamp,endTamp,*kw):
        data = rrdtool.fetch(widget.rrd.path(), "-s", str(startTamp), "-e",str(endTamp), "LAST")
        dt = {}
        data_def = eval(widget.data_def.replace("\r","").replace("\n",""))
        for i in range(len(data[1])):
            if data[1][i] in data_def.keys():
                dt[data[1][i]] = [i,data_def[data[1][i]]]
        return dt,data
    
    def getwidgeterrortimes(widget,dt,data,startTamp):
        rdt = {};
        class mythread(threading.Thread):
            def __init__(self,key,ddef,data,widget):
                self.index = ddef[0]
                self.data = data[2]
                self.time = data[0]
                self.key = key
                self.ddef = ddef[1]
                self.widget = widget
                self.startTamp = startTamp
                threading.Thread.__init__(self)
            def run(self):
                flag=False;flags=0.0;fl=False;fls=0.0;errorTimes=0;i=0;intervalFl=False
                good=[];normal=[];bad=[];gdef = self.ddef[1];bdef = self.ddef[2];
                goodAvg=0;normalAvg=0;badAvg=0;a=0;x=[];y=0;interval=5
                intervalErrorTime = [];errorTimeAvg = 0;allsAvg = 0;errorIntervalTimeAvg = 0
                for d in self.data:
                    i += 60
                    if d[self.index] != None:
                        if eval(str(d[self.index])+bdef):
                            bad.append(d[self.index])
                        elif eval(str(d[self.index])+gdef):
                            normal.append(d[self.index])
                            if intervalFl:
                                intervalErrorTime.append(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.time[0]+i)))
                                intervalFl = False
                        else:
                            good.append(d[self.index])
                            if intervalFl:
                                intervalErrorTime.append(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.time[0]+i)))
                                intervalFl = False
                        if not flag and eval(str(d[self.index])+bdef):
                            flag = True
                            flags += 1
                            a = 0
                        elif not eval(str(d[self.index])+bdef) and flag:
                           flag = False
                        if flag:
                            a += 1
                            if not fl and a >= interval:
                                fl = True
                                fls += 1
                                intervalErrorTime.append(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.time[0]+i-(interval-1)*60)))
                                intervalFl = True
                            elif a < interval and fl:
                                fl = False
                                x.append(y)
                            if fl:
                                y = a
                if fls != len(x):x.append(a)
                alls = good + normal + bad
                if flags != 0:errorTimeAvg = len(bad)/flags
                if fls != 0:errorIntervalTimeAvg = sum(x)/fls
                if len(good) != 0:goodAvg = sum(good)/len(good)
                if len(normal) != 0:normalAvg = sum(normal)/len(normal)
                if len(bad) != 0:badAvg = sum(bad)/len(bad)
                if len(alls) != 0:allsAvg = sum(alls)/len(alls)
                rdt[self.key+"_error_times"] = flags 
                rdt[self.key+"_error_avg"] = errorTimeAvg 
                rdt[self.key+"_error_interval_times"] = fls 
                rdt[self.key+"_error_interval_avg"] = errorIntervalTimeAvg
                rdt[self.key+"_good_times"] = len(good)
                rdt[self.key+"_good_avg"] = goodAvg
                rdt[self.key+"_normal_times"] = len(normal)
                rdt[self.key+"_normal_avg"] = normalAvg
                rdt[self.key+"_bad_times"] = len(bad)
                rdt[self.key+"_bad_avg"] = badAvg
                rdt[self.key+"_all_times"] = len(alls)
                rdt[self.key+"_all_avg"] = allsAvg
                rdt[self.key+"_interval_error_time"] = intervalErrorTime
                rdt["title"] = self.widget.title
                rdt["time"] = time.strftime("%Y-%m-%d",time.localtime(startTamp))
        threads = []
        for i in dt.keys():
            a = mythread(i,dt[i],data,widget)
            a.start()
            threads.append(a)
        for j in threads:
            j.join()
        s = StatisticsDay()
        s.widget = widget
        s.content = rdt
        s.date = time.strftime("%Y-%m-%d",time.localtime(startTamp))
        s.save()
    def parsewidget(widgets,startTamp):
        class mythreads(threading.Thread):
            def __init__(self,widget,startTamp):
                self.widget = widget
                self.startTamp = startTamp
                threading.Thread.__init__(self)
            def run(self):
                try:
                    dt,data = operation(self.widget,self.startTamp,self.startTamp+86400,"login","homepage")
                    getwidgeterrortimes(self.widget,dt,data,self.startTamp)
                except:
                    raise
                    pass
        mythr = []
        for w in widgets:
            mydate = time.strftime("%Y-%m-%d",time.localtime(startTamp))
            if len(StatisticsDay.objects.filter(date=mydate,widget=w.id)) == 0:
                aa = mythreads(w,startTamp)
                aa.start()
                mythr.append(aa)
        for j in mythr:
            j.join()
    end = request.GET.get("end",time.strftime("%Y-%m-%d"))
    start = request.GET.get("start","")
    endTamp = int(time.mktime(time.strptime(end,"%Y-%m-%d")))
    if start == "" or start == end:
        startTamp = endTamp - 86400
    else:
        startTamp = int(time.mktime(time.strptime(start,"%Y-%m-%d")))
    start = time.strftime("%Y-%m-%d",time.localtime(startTamp))
    widgets = Widget.objects.all()
    mystart = time.strftime("%Y-%m-%d %H:%M:%S")
    while startTamp < endTamp:
        for i in range(0,len(widgets),10):
            parsewidget(widgets[i:i+10],startTamp)
        startTamp += 86400
    myend = time.strftime("%Y-%m-%d %H:%M:%S")
    c = RequestContext(request,{
        "start":start,
        "end":end,
        "mystart":mystart,
        "myend":myend,
    })
    return render_to_response('servers/statistics.html',c)

def statistics_show_download(request):
    import time
    end = request.GET.get("end",time.strftime("%Y-%m-%d"))
    start = request.GET.get("start","")
    endTamp = int(time.mktime(time.strptime(end,"%Y-%m-%d")))
    if start == "" or start == end:
        startTamp = endTamp - 86400
    else:
        startTamp = int(time.mktime(time.strptime(start,"%Y-%m-%d")))
    start = time.strftime("%Y-%m-%d",time.localtime(startTamp))
    widgets = Widget.objects.all()
    statisticsDay = StatisticsDay.objects.filter(date__gte = start,date__lte=end)
    projects = ["shabik360","voda","zoota_vivas"];result = ["编号,项目,级别,报错widget,字段,开始时间,结束时间,解决办法"]
    x = 1
    for p in projects:
        grade = ["serious","major","minor"];ls = []
        for g in grade:
            wgls = widgets.filter(project__name=p,grade__title=g)
            slas = statisticsDay.filter(widget__in = wgls)
            for i in slas:
                try:
                    data = eval(i.content)
                    for k in data.keys():
                        if k.endswith("_interval_error_time"):
                            for l in range(0,len(data[k]),2):
                                tmp = [str(x)]
                                tmp.append(p)
                                tmp.append(g)
                                tmp.append(str(i.widget.title))
                                tmp.append(k.split("_in")[0])
                                tmp+=data[k][l:l+2]
                                ls.append(",".join(tmp))
                                x += 1
                except:
                     pass
        result.append("\n".join(ls)) 
    data = "\n".join(result)
    response = HttpResponse(data)
    response["content-type"] = "text/csv"
    response["content-disposition"] = "attachment; filename=error_report_"+start+"_"+end+".csv"
    return response
    
    
def statistics_show(request):
    import time
    end = request.GET.get("end",time.strftime("%Y-%m-%d"))
    start = request.GET.get("start","")
    endTamp = int(time.mktime(time.strptime(end,"%Y-%m-%d")))
    if start == "" or start == end:
        startTamp = endTamp - 86400
    else:
        startTamp = int(time.mktime(time.strptime(start,"%Y-%m-%d")))
    start = time.strftime("%Y-%m-%d",time.localtime(startTamp))
    widgets = Widget.objects.all()
    statisticsDay = StatisticsDay.objects.filter(date__gte = start,date__lte=end)
    projects = ["shabik360","voda","zoota_vivas"];sla=[];errors=[];toperror=[]
    for p in projects:
        tmp = {"p":p}
        wgls = widgets.filter(project__name=p,service_type__name="sla")
        slas = statisticsDay.filter(widget__in = wgls)
        login_bad_times=0;homepage_bad_times=0;login_all_times=0;homepage_all_times=0;keyong=0
        for i in slas:
            data = eval(i.content)
            try:
                login_bad_times += data['login_bad_times']
                homepage_bad_times += data['homepage_bad_times']
                homepage_all_times += data['homepage_bad_times']
                login_all_times += data['login_all_times']
            except:
                pass
        badTimes = login_bad_times+homepage_bad_times
        allTimes = login_all_times+homepage_all_times
        if allTimes != 0:
            keyong = 1-badTimes/float(allTimes)
        tmp["badTime"]=badTimes
        tmp["keyong"]=str(keyong*100)[:5]+"%"
        sla.append(tmp)
    for p in projects:
        grade = ["major","minor","serious"];tmppro = {"p":p}; tmpgrade={}
        for g in grade:
            tmp={};solveTime=[];solveTimeAvg=0;error_times=[]
            wgls = widgets.filter(project__name=p,grade__title=g)
            slas = statisticsDay.filter(widget__in = wgls)
            for i in slas:
                try:
                    data = eval(i.content)
                    for k in data.keys():
                        if k.endswith("error_interval_times"):
                            error_times.append(data[k])
                        elif k.endswith("error_interval_avg"):
                            if data[k] != 0:
                                solveTime.append(data[k])
                except:
                     pass
            if solveTime != []:
               solveTimeAvg = float(sum(solveTime))/len(solveTime)
            tmp["error_times"] = sum(error_times)
            tmp["solveTimeAvg"] = str(solveTimeAvg)[:5]
            tmpgrade[g] = tmp
        tmppro["grade"] = tmpgrade
        errors.append(tmppro)
    serviceType = WidgetServiceType.objects.all()
    for p in projects:
        for s in serviceType:
            dt = {"project":p,"service":s.name}
            wgls = widgets.filter(project__name=p,service_type=s)
            slas = statisticsDay.filter(widget__in = wgls)
            error_times = 0
            for i in slas:
                try:
                    data = eval(i.content)
                    for k in data.keys():
                        if k.endswith("error_times"):
                            error_times += data[k]
                except:
                    pass
            dt["error_times"] = error_times
            toperror.append(dt)
    toperror = sorted(toperror,key=lambda l:l["error_times"],reverse = True)
    c = RequestContext(request,{
        "start":start,
        "end":end,
        "sla":sla,
        "errors":errors,
        "toperror":toperror[:10],
    })
    return render_to_response('servers/statistics_show.html',c)
