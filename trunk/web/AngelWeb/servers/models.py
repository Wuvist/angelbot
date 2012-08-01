# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.conf import settings

SERVER_TYPE_CHOICES = (
    ('W', 'Windows'),
    ('L', 'Linux'),
)

PHYSICAL_SERVER_CHOICES = (
    ('Y', 'Yes'),
    ('N', 'No'),
)

SERVER_FUNCTION_CHOICES = (
    ('D', 'DB'),
    ('A', 'APP'),
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

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=50)
    alarm = models.CharField(max_length=8, choices=ALARM_TYPE_CHOICES)
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
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    project = models.ForeignKey(Project)
    physical_server = models.CharField(max_length=1, choices=PHYSICAL_SERVER_CHOICES)
    physical_server_ip = models.IPAddressField(max_length=200)
    core = models.IntegerField(max_length=2)
    ram = models.CharField(max_length=10)
    hard_disk = models.CharField(max_length=100)
    server_function = models.CharField(max_length=1, default="A", choices=SERVER_FUNCTION_CHOICES)
    server_type = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    idc = models.ForeignKey(IDC)
    remark = models.CharField(max_length=256, null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.name + "(" + str(self.ip) + ")"
    
    class Meta:
        ordering = ["ip"]

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

class SeverCmd(models.Model):
    server = models.ForeignKey(Server)
    cmd = models.ForeignKey(Cmd)
    title = models.CharField(max_length=256)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

class Dashboard(models.Model):
    title = models.CharField(max_length=50)
    user = models.ManyToManyField(User, null = True, blank=True)
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
class WidgetCategory(models.Model):
    title = models.CharField(max_length=64, )
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

WIDGET_TYPE_CHOICES = (
    ('1', 'Show Current Value Only'),
    ('2', 'Show Current / Yesterday / Last Week Value'),
)

class Widget(models.Model):
    title = models.CharField(max_length=50)
    dashboard = models.ManyToManyField(Dashboard)
    server = models.ForeignKey(Server, null = True, blank=True)
    rrd = models.ForeignKey(Rrd)
    category = models.ForeignKey(WidgetCategory)
    grade = models.ForeignKey(WidgetGrade, null = True, blank=True)
    widget_type = models.CharField(max_length=1, choices=WIDGET_TYPE_CHOICES)
    project = models.ManyToManyField(Project)
    service_type = models.ForeignKey(WidgetServiceType, null = True, blank = True)
    graph_def = models.TextField(max_length =512)
    data_def = models.TextField(max_length =512, null = True, blank=True)
    path = models.CharField(max_length=128, null = True, blank=True)
    remark = models.CharField(max_length=256, null = True, blank = True)
    update_time = models.DateTimeField(null = True, blank = True)
    created_on = models.DateTimeField(auto_now_add = True)
    def __unicode__(self):
        return self.title + "-----" + self.rrd.name
    
    class Meta:
        ordering = ["title"]

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
    widget = models.ManyToManyField(Widget)
    
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
    contact_result = models.CharField(max_length=8,null = True, blank = True)
    result = models.TextField(null = True, blank = True)
    overdue = models.CharField(max_length=1, choices=ALARMLOG_OVERDUE_CHOICES)
    created_on = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.title) + ": "  + str(self.alarmlevel) +" level "+ str(self.widget) + " (" + str(self.created_on)  +")"

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
    graphs = models.ManyToManyField(GraphAiderDef, null = True, blank = True)
    width = models.IntegerField(max_length=50)
    height = models.IntegerField(max_length=50)
    refresh_time = models.IntegerField(max_length=50)
    user = models.ManyToManyField(User, null = True, blank=True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ["title"]

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

