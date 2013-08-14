#!/usr/bin/env python
# encoding: utf-8
"""
views.py

Created by Wuvist on 2010-07-01.
Copyright (c) 2010 . All rights reserved.
"""
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from servers.models import *
import time

@login_required()
def home(request):
    win_servers = Server.objects.filter(server_type="W").all()
    linux_servers = Server.objects.filter(server_type="L").all()
    graph_aiders = GraphAider.objects.filter(user=request.user.id).all()
    if request.user.is_superuser:
        dashboards = Dashboard.objects.all()
        error_dashboards = DashboardError.objects.all()
    else:
        dashboards = request.user.dashboard_set.all()
        error_dashboards = request.user.dashboarderror_set.all()
    is_staff = False
    if dashboards[0].id == 1:
        is_staff = True

    c = RequestContext(request, 
        {"win_servers":win_servers, 
        "linux_servers": linux_servers,
        "dashboards": dashboards,
        "is_staff": is_staff,
        "graph_aiders":graph_aiders,
        "error_dashboards":error_dashboards,
        })
    return render_to_response('home.html',c)


def dba_show_backup(request):
    import json
    def sendmail(c,n,s):
        import smtplib
        from email.mime.text import MIMEText

        des = "\n\nThis email auto send by Mozat Angel, if any questions, please kindly feed back to operation team. thanks !\nBest Regards\nMozat Angel"
        sender = 'wumingyou@mozat.com'
        msg = MIMEText("Dear,\n\n%s backup error happened,please visit bleow url for more details\n http://angel.morange.com/dba/backlog/%s"  % (c,des))
        msg['Subject'] = "[DB backup] %s" % s
        msg['From'] = "Mozat Angel"
        msg['To'] = n
        s = smtplib.SMTP('i-smtp.mozat.com')
        s.sendmail(sender, n.split(";"), msg.as_string())
        s.close()

    def addError(k,edit=False):
        if edit:
            if errorData.has_key(k):
                errorData[k]["times"].append(t)
                errorData[k]["times"] = list(set(errorData[k]["times"]))
            else:errorData[k] = {"send":False,"times":[t]}
        else:
            try:del errorData[k]
            except:pass

    if request.GET.has_key("remark"):
        i = request.GET["id"]
        r = request.GET["remark"]
        log,created = ExtraLog.objects.get_or_create(type=2,label=i,defaults={"label":i,"value":r,"type":2})
        if not created:
            log.value = r
            log.save()
        return HttpResponseRedirect("/dba/backlog/")
    t = time.strftime("%Y%m%d%H%M")
    try:
        errorDataLog = ExtraLog.objects.get(type=4)
        errorData = json.loads(errorDataLog.value)
    except:errorData = {}
    def parserLog(infoLog,detailLog):
        result = []
        try:data = open(detailLog).read().split("\n\n")
        except:data = []
        for i in open(infoLog).readlines():
            i = ["","",""] + i.split(",")
            if len(i) < 7:continue
            i[3] = i[3].replace("_",":")
            i[4] = i[4].replace("_",":")
            try:
                log = ExtraLog.objects.get(type=2,label=i[3]+"_"+i[4])
                i[0] = log.value
            except:pass
            for d in data:
                if i[3] in d and i[3] != "":
                    i[1] = d.replace(" ","&nbsp;&nbsp;").replace("\n","<br>")
                    continue
                if i[4] in d and i[4] != "":
                    i[2] = d.replace(" ","&nbsp;&nbsp;").replace("\n","<br>")
                    continue
            try:i[9] = int(i[9][:-1])
            except:pass
            result.append(i)
            try:
                timeDiff = time.time() - time.mktime(time.strptime(i[6], "%Y-%m-%d %H:%M:%S"))
                if i[14] == "full":timeDiffConf = 30*24*60*60+1200
                else:timeDiffConf = 24*60*60+1200
                if "ERROR" in i[5] or "ERROR" in i[7] or i[9] > 95 or timeDiff > timeDiffConf:
                    addError(i[3]+"-"+i[4],edit=True)
                    if len(errorData[i[3]+"-"+i[4]]["times"]) > settings.DB_ERROR_TIME and errorData[i[3]+"-"+i[4]]["send"] == False:
                        sendmail(i[3]+"-"+i[4],settings.DB_RECEIVER,i[3]+"-"+i[4])
                        errorData[i[3]+"-"+i[4]]["send"] = True
                else:addError(i[3]+"-"+i[4])
            except:
                pass
        return result
    mysqlData = parserLog(settings.DB_MYSQL_INFO_LOG,settings.DB_MYSQL_DETAIL_LOG)
    sqlserverData = parserLog(settings.DB_SQLSERVER_INFO_LOG,settings.DB_SQLSERVER_DETAIL_LOG)
    try:
        errorDataLog.value = json.dumps(errorData)
        errorDataLog.save()
    except:
        log = ExtraLog(type=4,value=json.dumps(errorData)).save()

    return render_to_response("dba_show_backuplog.html",{"mysqlData":mysqlData,"sqlserverData":sqlserverData})
