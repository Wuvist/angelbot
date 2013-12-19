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
from django.http import HttpResponse, HttpResponseRedirect
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
                timeDay = int(time.strftime("%w"))
                if timeDay == 0:timeDay = 7
                timeDiff = time.time() - time.mktime(time.strptime(i[6], "%Y-%m-%d %H:%M:%S"))
                if i[14] == "full":timeDiffConf = 30*24*60*60+1200
                else:timeDiffConf = 2*24*60*60+1200
                backupDayResult = False
                if timeDay >=2:
                    backupDayDt = {}
                    for backupDay in i[11].split("-"):
                        backupDay = backupDay.split(":")
                        backupDayDt[int(backupDay[0])] = backupDay[1]
                    if backupDayDt[timeDay] == "N" and backupDayDt[timeDay-1] == "N":backupDayResult = True
                if "ERROR" in i[5] or "ERROR" in i[7] or i[9] > 95 or timeDiff > timeDiffConf or backupDayResult:
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
    try:remoteData = [i.split(",") for i in open(settings.DB_REMOTE_BACKUP).readlines()]
    except:remoteData = []
    return render_to_response("dba_show_backuplog.html",{"mysqlData":mysqlData,"sqlserverData":sqlserverData,"remoteData":remoteData})


@login_required
def diff_netword_cfg(request):
    import os
    import re
    import json
    import urllib2
    
    if "tid" in request.GET:
        try:
            if request.GET["tid"] == "":
                ExtraLog.objects.get(type=5,label=request.GET["date"]).delete()
        except:return HttpResponseRedirect("/netcfg/diff/")
        tid = request.GET["tid"].replace(","," ").strip()
        try:
            log = ExtraLog.objects.get(type=5,label=request.GET["date"])
            log.value = tid
            log.save()
        except:
            log = ExtraLog()
            log.type = 5
            log.label = request.GET["date"]
            log.value = tid
            log.save()
        return HttpResponseRedirect("/netcfg/diff/")
    
    def execute_cmd(cmd):
        cmd = "svn --username %s --password %s --no-auth-cache %s %s" % (settings.SVN_USERNAME,settings.SVN_PASSWORD,cmd,settings.SVN_NETWORK_CONFIG)
        data = os.popen(cmd).read().replace("\r","").strip()
        return data
    data = {};svnDt = {}; svnLs = [];dates = [];ticketsDt = {};ticketIdDt = {};result = []
    for i in execute_cmd("info").split("\n"):
        try:
            i = i.split(": ")
            data[i[0]] = i[1]
        except:pass
    lastRev = int(data["Last Changed Rev"])
    for i in range(lastRev,lastRev-settings.SVN_DIFF_NUMBER,-1):
        tmpDt = {};tmpLs = []
        data = execute_cmd("diff -r %s:%s" % (i-1,i))
        if "--- 2.1" in data and data.count("---") == 1:continue
        for j in re.sub("--- 2\.1.+---","",data.replace("\n","<br>").replace("\t","    ")).split("<br>"):
            #if j.startswith("@") or j.startswith("-") or j.startswith("+"):
             if j.startswith("---") or "@@ -1,4 +1,4 @@" in j or "#############" in j:continue
             elif j.startswith("+++"):tmpLs.append(re.findall("\+\+\+ (.+)  ",j)[0])
             elif j.startswith("@"):tmpLs.append(j)
             elif j.startswith("-"):tmpLs.append(j)
             elif j.startswith("+"):tmpLs.append(j)
        tmpDt["content"] = tmpLs
        d = execute_cmd("info -r %s" % i)
        i = d.index("Last Changed Date: ")
        changedTime = d[i+19:i+39]
        tmpDt["changedTime"] = changedTime
        tmpDt["changedDate"] = changedTime[:10]
        dates.append(tmpDt["changedDate"])
        svnLs.append(tmpDt)
        svnDt[tmpDt["changedDate"]] = tmpDt
    try:
        tickets = json.loads(urllib2.urlopen(settings.TICKET_API % (svnLs[-1]["changedDate"],svnLs[0]["changedDate"])).read())
    except:
        tickets = []
    for t in tickets:
        dates.append(t["created_date"])
        ticketsDt.setdefault(t["created_date"],[]).append(t)
        ticketIdDt[t["id"]] = t
    dates = list(set(dates))
    dates.sort()
    dates.reverse()
    relatedTicket = []
    for i in ExtraLog.objects.filter(type=5,label__in=dates):
        relatedTicket += i.value.split()
    for d in dates:
       tmp = {"ticket":[]}
       if d in svnDt:tmp["svn"] = svnDt[d]
       try:
           log = ExtraLog.objects.get(type=5,label=d)
           for i in log.value.split():
               tmp["ticket"].append(ticketIdDt[i])
           tmp["relatedTicket"] = log.value
       except:log = None
       if d in ticketsDt:
           for i in ticketsDt[d]:
               if i["id"] not in relatedTicket:
                   tmp["ticket"].append(i)
       if tmp["ticket"] != [] or "svn" in tmp:
           tmp["date"] = d
           result.append(tmp)
    return render_to_response("netcfg_diff.html",{"data":result})
    

@login_required()
def control_call(request):
    try:
        log = ExtraLog.objects.filter(type=6)[0]
        call = log.value
    except:
        log = ExtraLog(type=6)
        call = "off"
    if request.GET.has_key("call"):
        c = request.GET.get("call","")
        if c == "on":
            log.value = "on"
            log.save()
            call == "on"
        elif c == "off":
            log.value = "off"
            log.save()
            call == "off"
        l = DisableAlarmLog(action=c,name=request.user.username)
        l.save()
        return HttpResponseRedirect("./")
    if call == "on":
        return HttpResponse('<center><input type="button" style="width:500px;height:250px;" onclick="javascript: location.href = \'./?call=off\'" value = "On" /></center>')
    else:return HttpResponse('<center><input type="button" style="width:500px;height:250px;" onclick="javascript: location.href = \'./?call=on\'" value = "Off" /></center>')
