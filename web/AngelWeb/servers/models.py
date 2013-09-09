# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.conf import settings

SERVER_TYPE_CHOICES = (
    ('W', 'Windows'),
    ('L', 'Linux'),
    ('V', 'VMware'),
)

PHYSICAL_SERVER_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No'),
)

SERVER_FUNCTION_CHOICES = (
    (1, 'Monet'),
    (2, 'APP'),
    (3, 'DB'),
    (4, 'VMware'),
)

ALARM_TYPE_CHOICES = (
    ('True', 'True'),
    ('False', 'False'),
)

SERVICETYPE_COLOR_CHOICES = (
    ('antiquewhite','antiquewhite'),('blue','blue'),('brown','brown'),('coral','coral'),('gray','gray'),('green','green'),
    ('lightblue','lightblue'),('lightcoral','lightcoral'),('lightcyan','lightcyan'),('lightgreen','lightgreen'),
    ('lightgrey','lightgrey'),('lightpink','lightpink'),('lightskyblue','lightskyblue'),('lightyellow','lightyellow'),
    ('orange','orange'),('orchid','orchid'),('red','red'),('teal','teal'),('yellow','yellow'),
)

REMARK_LOG_CHOICES = (
    (1, 'cpu_ram_io'),
    (2, 'server ping'),
    (3, 'db show backup'),
    (4, 'ignore widget config'),
)

WIDGET_TYPE_CHOICES = (
    ('1', 'Show Current Value Only'),
    ('2', 'Show Current / Yesterday / Last Week Value'),
)

class Project(models.Model):
    name = models.CharField(max_length=50)
    alarm = models.CharField(max_length=8, choices=ALARM_TYPE_CHOICES)
    sequence = models.IntegerField(max_length=10, null = True, blank = True)
    remark = models.CharField(max_length=1000, null = True, blank = True)
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

class IDC(models.Model):
    name = models.CharField(max_length=50)
    remark = models.CharField(max_length=1000, null = True, blank = True)
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

class Server(models.Model):
    ip = models.IPAddressField(max_length=200)
    name = models.CharField(max_length=50, unique = True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    project = models.ManyToManyField(Project, null = True, blank = True)
    physical_server = models.CharField(max_length=1, choices=PHYSICAL_SERVER_CHOICES)
    physical_server_ip = models.IPAddressField(max_length=200)
    core = models.IntegerField(max_length=2)
    ram = models.CharField(max_length=10)
    hard_disk = models.CharField(max_length=100)
    uid = models.CharField(max_length=250, unique = True)
    rack = models.CharField(max_length=1000, null = True, blank = True)
    label = models.CharField(max_length=1000, null = True, blank = True)
    server_function = models.IntegerField(max_length=2, default=2, choices=SERVER_FUNCTION_CHOICES)
    server_type = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    idc = models.ForeignKey(IDC)
    idle = models.CharField(max_length=1, default='N',choices=PHYSICAL_SERVER_CHOICES)
    power_on = models.CharField(max_length=1, default='Y',choices=PHYSICAL_SERVER_CHOICES)
    remark = models.CharField(max_length=256, null = True, blank = True)
    perf = models.TextField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.name + "(" + str(self.ip) + ")"
    
    class Meta:
        ordering = ["ip"]

#type 1:deployment parser
#type 2:db backup log
#type 3:cmdb show service user page size
#type 4:db error mark
#type 5:network config diff
class ExtraLog(models.Model):
    mark = models.IntegerField(max_length=10,null = True, blank = True)
    type = models.IntegerField(max_length=8)
    label = models.CharField(max_length=256,null = True, blank = True)
    sign = models.CharField(max_length=64,null = True, blank = True)
    value = models.TextField(null = True, blank = True)
    created_on = models.DateField(null = True, blank = True)
    created_time = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.type) + " " + str(self.mark)

class RemarkLog(models.Model):
    mark = models.IntegerField(max_length=10,null = True, blank = True)
    type = models.IntegerField(max_length=8,choices=REMARK_LOG_CHOICES,null = True, blank = True)
    label = models.CharField(max_length=64,null = True, blank = True)
    sign = models.CharField(max_length=64,null = True, blank = True)
    value = models.TextField(null = True, blank = True)
    created_on = models.DateField(auto_now_add= True)
    created_time = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.type) + " " + str(self.mark)

class CmdLog(models.Model):
    user = models.ForeignKey(User)
    cmd = models.CharField(max_length=200)
    result = models.TextField()    
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.user) + ":" + self.cmd + "(" + str(self.created_on)  +")"

class Cmd(models.Model):
    server_type = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    text = models.CharField(max_length=200)
    def __unicode__(self):
        return self.text
    
    class Meta:
        ordering = ["text"]

class Rrd(models.Model):
    name = models.CharField(max_length=50)
    setting = models.TextField(max_length=512)
    des = models.CharField(max_length=256)
    
    def path(self):
        return str(settings.RRD_PATH + self.name + ".rrd")
    
    def __unicode__(self):
        return self.name + " " + self.des
    
    class Meta:
        ordering = ["name"]

class GraphAiderDef(models.Model):
    title = models.CharField(max_length=50)
    rrd = models.ForeignKey(Rrd)
    graph_type = models.CharField(max_length=1, choices=WIDGET_TYPE_CHOICES)
    lines_def = models.TextField(max_length=256)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]
        
class GraphAider(models.Model):
    title = models.CharField(max_length=50)
    sequence = models.IntegerField(max_length=10, null = True, blank = True)
    graphs = models.ManyToManyField(GraphAiderDef, null = True, blank = True)
    width = models.IntegerField(max_length=50)
    height = models.IntegerField(max_length=50)
    refresh_time = models.IntegerField(max_length=50)
    user = models.ManyToManyField(User, null = True, blank=True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]
class SeverCmd(models.Model):
    server = models.ForeignKey(Server)
    cmd = models.ForeignKey(Cmd)
    title = models.CharField(max_length=256)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

class AlarmServerCmd(models.Model):
    title = models.CharField(max_length = 250, unique = True)
    default_cmd = models.ForeignKey(Cmd)
    server_cmd = models.ManyToManyField(SeverCmd,null = True, blank = True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

class Dashboard(models.Model):
    title = models.CharField(max_length=50)
    user = models.ManyToManyField(User, null = True, blank=True)
    sequence = models.IntegerField(max_length=10,null = True, blank=True)
    graphs = models.ManyToManyField(GraphAiderDef)
    width = models.IntegerField(max_length=8)
    height = models.IntegerField(max_length=8)
    des = models.TextField(max_length =512, null = True, blank=True)
    
    def __unicode__(self):
        return self.title

CATEGORY_DISPLAY_CHOICES = (
    ('black', 'True'),
    ('none', 'False'),
)
CATEGORY_DISPLAY_MODE_CHOICES = (
    ('0', 'Error & Warning'),
    ('1', 'Error'),
)


class WidgetCategoryTemplate(models.Model):
    rrd_setting = models.TextField()
    widget_graph = models.TextField()
    widget_data = models.TextField()
    
    def __unicode__(self):
        return str(self.id)

class WidgetCategory(models.Model):
    title = models.CharField(max_length=64)
    template = models.ForeignKey(WidgetCategoryTemplate, null=True, blank=True)
    display = models.CharField(max_length=8, choices=CATEGORY_DISPLAY_CHOICES)
    display_mode = models.CharField(max_length=1, choices=CATEGORY_DISPLAY_MODE_CHOICES)
    des = models.TextField(null = True, blank=True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]
        
class ServiceType(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=16, choices=SERVICETYPE_COLOR_CHOICES)
    remark = models.CharField(max_length=256, null = True, blank = True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

class WidgetServiceType(models.Model):
    name = models.CharField(max_length=50)
    type = models.ForeignKey(ServiceType)
    show_key = models.TextField(null = True, blank=True)
    remark = models.CharField(max_length=256, null = True, blank = True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

class WidgetGrade(models.Model):
    title = models.CharField(max_length=50)
    remark = models.CharField(max_length=256, null = True, blank = True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

class Widget(models.Model):
    title = models.CharField(max_length=50)
    dashboard = models.ManyToManyField(Dashboard)
    server = models.ForeignKey(Server, null = True, blank=True)
    rrd = models.ForeignKey(Rrd)
    category = models.ForeignKey(WidgetCategory)
    grade = models.ForeignKey(WidgetGrade)
    widget_type = models.CharField(max_length=1, choices=WIDGET_TYPE_CHOICES)
    project = models.ManyToManyField(Project)
    service_type = models.ForeignKey(WidgetServiceType, null = True, blank = True)
    graph_def = models.TextField(max_length =512)
    data_def = models.TextField(max_length =512, null = True, blank=True)
    data_default = models.TextField(max_length =512, null = True, blank=True)
    path = models.CharField(max_length=128, null = True, blank=True)
    remark = models.CharField(max_length=256, null = True, blank = True)
    update_time = models.DateTimeField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    def __unicode__(self):
        return self.title + "-----" + self.rrd.name
    
    class Meta:
        ordering = ["title"]

class DetectorInfo(models.Model):
    widget = models.ForeignKey(Widget)
    data = models.TextField(null = True, blank = True)
    created_time = models.DateTimeField(auto_now_add = True)

class StatisticsDay(models.Model):
    widget = models.ForeignKey(Widget)
    content = models.TextField(max_length = 10240,null = True, blank = True)
    remark = models.CharField(max_length=256, null = True, blank = True)
    date = models.DateField()
    
    def __unicode__(self):
        return self.widget.title

class AlarmUser(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    address = models.CharField(max_length=50, null = True, blank = True)
    des = models.CharField(max_length=50, null = True, blank = True)
    
    def __unicode__(self):
        return self.name + " " + self.phone
    
    class Meta:
        ordering = ["name"]

class Alarm(models.Model):
    title = models.CharField(max_length=50)
    enable = models.CharField(max_length=8, choices=ALARM_TYPE_CHOICES)
    alarm_def = models.TextField(max_length =512, null = True, blank = True)
    des = models.TextField(max_length =512, null = True, blank = True)    
    firstcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'firstcontact_set')
    secondcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'secondcontact_set')
    thirdcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'thirdcontact_set')
    fourthcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'fourthcontact_set')
    fifthcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'fifthcontact_set')
    sixthcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'sixthcontact_set')
    widget = models.ManyToManyField(Widget,limit_choices_to={'dashboard__id':1})
    
    def __unicode__(self):
        return self.title + " " + self.enable
    
    class Meta:
        ordering = ["title"]

ALARMLOG_OVERDUE_CHOICES = (
    ('1', 'Not'),
    ('2', 'Yes'),
)

class AlarmLog(models.Model):
    title = models.ForeignKey(Alarm)
    widget = models.ForeignKey(Widget)
    alarmlevel = models.IntegerField(max_length=1)
    alarmmode = models.CharField(max_length=16)
    ticketid = models.CharField(max_length=16, null = True, blank = True)
    alarmuser = models.ManyToManyField(AlarmUser, null = True, blank = True)
    result = models.TextField(null = True, blank = True)
    contact_result = models.TextField(null = True, blank = True)
    overdue = models.CharField(max_length=1, choices=ALARMLOG_OVERDUE_CHOICES)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.title) + ": "  + str(self.alarmlevel) +" level "+ str(self.widget) + " (" + str(self.created_on)  +")"


class FrequentAlarm(models.Model):
    title = models.CharField(max_length=50)
    enable = models.CharField(max_length=8, choices=ALARM_TYPE_CHOICES)
    alarm_def = models.TextField(max_length =512, null = True, blank = True)
    des = models.TextField(max_length =512, null = True, blank = True)    
    firstcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'FrequentAlarm_firstcontact_set')
    secondcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'FrequentAlarm_secondcontact_set')
    thirdcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'FrequentAlarm_thirdcontact_set')
    fourthcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'FrequentAlarm_fourthcontact_set')
    fifthcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'FrequentAlarm_fifthcontact_set')
    sixthcontact = models.ManyToManyField(AlarmUser, null = True, blank = True, related_name = 'FrequentAlarm_sixthcontact_set')
    widget = models.ManyToManyField(Widget)
    
    def __unicode__(self):
        return self.title + " " + self.enable
    
    class Meta:
        ordering = ["title"]

class FrequentAlarmLog(models.Model):
    title = models.ForeignKey(FrequentAlarm)
    widget = models.ForeignKey(Widget)
    lasterror = models.CharField(max_length=8, choices=ALARM_TYPE_CHOICES)
    error_num = models.IntegerField(max_length=16, null = True, blank = True)
    alarmlevel = models.IntegerField(max_length=1, null = True, blank = True)
    alarmmode = models.CharField(max_length=16, null = True, blank = True)
    ticketid = models.CharField(max_length=16, null = True, blank = True)
    alarmuser = models.ManyToManyField(AlarmUser, null = True, blank = True)
    contact_result = models.CharField(max_length=8,null = True, blank = True)
    result = models.TextField(null = True, blank = True)
    lasterror_time = models.DateTimeField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.title) + ": "  + str(self.alarmlevel) +" level "+ str(self.widget) + " (" + str(self.created_on)  +")"

class DashboardError(models.Model):
    title = models.CharField(max_length=50)
    dashboard = models.ForeignKey(Dashboard)
    graphs = models.ManyToManyField(GraphAiderDef)
    width = models.IntegerField(max_length=8)
    height = models.IntegerField(max_length=8)
    user = models.ManyToManyField(User, null = True, blank=True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

TICKET_ACTION_CHOICES = (
    ('action', 'action'),
    ('comment', 'comment'),
)

class TicketAction(models.Model):
    user = models.ForeignKey(User)
    actiontype = models.CharField(max_length=20, choices=TICKET_ACTION_CHOICES)
    action = models.TextField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.action
    
    class Meta:
        ordering = ["-created_on"]
    
class TicketHistory(models.Model):
    user = models.ForeignKey(User)
    content = models.TextField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.content

    class Meta:
        ordering = ["-created_on"]

TICKET_STATUS_CHOICES = (
    ('New', 'New'),
    ('Processing', 'Processing'),
    ('Closed','Closed'),
    ('Done','Done'),
)

class Ticket(models.Model):
    title = models.CharField(max_length=200)
    widget = models.ForeignKey(Widget, null = True, blank = True)
    assignto = models.ForeignKey(User, null = True, blank = True, related_name = 'Ticket_assignto_set')
    recorder = models.ForeignKey(User, related_name = 'Ticket_recorder_set')
    service = models.ForeignKey(WidgetServiceType)
    status = models.CharField(max_length=20, choices=TICKET_STATUS_CHOICES)
    incident = models.TextField(null = True, blank = True)
    incidenttype = models.CharField(max_length=20,null = True, blank = True)
    incidentgrade = models.CharField(max_length=20,null = True, blank = True)
    project = models.ManyToManyField(Project, null = True, blank = True)
    action = models.ManyToManyField(TicketAction,null = True, blank = True)
    history = models.ManyToManyField(TicketHistory,null = True, blank = True)
    starttime = models.DateTimeField(auto_now_add = True)
    lastupdate = models.DateTimeField(auto_now = True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

class StatisticsComment(models.Model):
    user = models.ForeignKey(User)
    comment_type = models.CharField(max_length=64)
    content = models.TextField(null = True, blank = True)
    comment_time = models.TextField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.comment_type+" "+self.content

    class Meta:
        ordering = ["-created_on"]

class BackupLogRemark(models.Model):
    content = models.TextField(null = True, blank = True)
    created_on = models.DateField(auto_now_add = True)
    
    def __unicode__(self):
        return self.content

class BackupLogMail(models.Model):
    name = models.CharField(max_length = 50,null = True, blank = True)
    log_date = models.CharField(max_length = 128,null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.name

class BackupLog(models.Model):
    name = models.CharField(max_length=64, null = True, blank = True)
    email= models.CharField(max_length=64, null = True, blank = True)
    log_type = models.CharField(max_length=64, null = True, blank = True)
    log_name = models.CharField(max_length=64, null = True, blank = True)
    remark = models.ManyToManyField(BackupLogRemark,null = True, blank = True)
    mail = models.ManyToManyField(BackupLogMail,null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.log_name+"  "+self.name
    
    class Meta:
        ordering = ["-created_on"]

class AlarmTest(models.Model):
    user = models.ForeignKey(User)
    result = models.TextField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = False)
    
    def __unicode__(self):
        return self.user.username + " " + str(self.created_on) + " " + str(self.result)

class SshName(models.Model):
    name = models.CharField(max_length=256)
    fingerprint = models.CharField(max_length=256)
    key = models.TextField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = False)
    
    def __unicode__(self):
        return self.name

class SshLog(models.Model):
    name = models.CharField(max_length=256)
    logname = models.CharField(max_length=256)
    flag = models.CharField(max_length=256)
    fingerprint = models.CharField(max_length=256)
    ip = models.CharField(max_length=256)
    ips = models.TextField(null = True, blank = True)
    date = models.DateTimeField()
    created_on = models.DateTimeField(auto_now_add = False)
    
    def __unicode__(self):
        return self.name + " " + str(self.created_on)
