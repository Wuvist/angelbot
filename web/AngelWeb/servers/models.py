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
        return self.name    
    
    
class CmdLog(models.Model):
    user = models.ForeignKey(User)
    cmd = models.CharField(max_length=200)
    created_on = models.DateTimeField(auto_now_add = True)
    
    
class Cmd(models.Model):
    server_type = models.CharField(max_length=1, choices=SERVER_TYPE_CHOICES)
    text = models.CharField(max_length=200)
    def __unicode__(self):
        return self.text
        
class Rrd(models.Model):
    name = models.CharField(max_length=50)
    setting = models.TextField(max_length=512)
    des = models.CharField(max_length=256)
    
    def path(self):
        return str(settings.RRD_PATH + self.name + ".rrd")
    
    def __unicode__(self):
        return self.name + " " + self.des
        
class SeverCmd(models.Model):
    server = models.ForeignKey(Server)
    cmd = models.ForeignKey(Cmd)
    title = models.CharField(max_length=256)
    
    def __unicode__(self):
        return title

class Dashboard(models.Model):
    title = models.CharField(max_length=50)

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
    cmd = models.ForeignKey(Cmd, null = True, blank=True)
        
    def __unicode__(self):
        return self.title