from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.conf import settings

SERVER_TYPE_CHOICES = (
    ('W', 'Windows'),
    ('L', 'Linux'),
)

# Create your models here.
class Server(models.Model):
    ip = models.IPAddressField(max_length=200)
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    server_type = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    remark = models.CharField(max_length=1000)
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

WIDGET_TYPE_CHOICES = (
    ('1', 'Show Current Value Only'),
    ('2', 'Show Current / Yesterday / Last Week Value'),
)

class Widget(models.Model):
    title = models.CharField(max_length=50)
    dashboard = models.ManyToManyField(Dashboard)
    server = models.ForeignKey(Server, null = True, blank=True)
    rrd = models.ForeignKey(Rrd)
    category = models.CharField(max_length =50, null = True, blank=True)
    widget_type = models.CharField(max_length=1, choices=WIDGET_TYPE_CHOICES)
    graph_def = models.TextField(max_length =512)
    data_def = models.TextField(max_length =512, null = True, blank=True)
        
    def __unicode__(self):
        return self.title + "-----" + self.rrd.name
    
    class Meta:
        ordering = ["title"]

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

ALARM_TYPE_CHOICES = (
    ('True', 'True'),
    ('False', 'False'),
)

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

