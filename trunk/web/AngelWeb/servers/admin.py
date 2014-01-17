#!/usr/bin/env python
# encoding: utf-8
"""
admin.py

Created by Wuvist on 2010-07-01.
Copyright (c) 2010 . All rights reserved.
"""

from django.contrib import admin
from AngelWeb.servers.models import *
from django.forms import ModelForm, PasswordInput
from django.http import HttpResponse, HttpResponseRedirect
from subprocess import Popen, PIPE
from django.conf import settings
import time





def projectChangeAlarmOff(self, request, queryset):
    rowsUpdated = queryset.update(alarm='False')
    if rowsUpdated == 1:ms = "1 project was"
    else:ms = "%s projects were" % rowsUpdated
    self.message_user(request, "%s successfully changed alarm Off." % ms)
projectChangeAlarmOff.short_description = "Change selected projects alarm Off"

def projectChangeAlarmOn(self, request, queryset):
    rowsUpdated = queryset.update(alarm='True')
    if rowsUpdated == 1:ms = "1 project was"
    else:ms = "%s projects were" % rowsUpdated
    self.message_user(request, "%s successfully changed alarm On." % ms)
projectChangeAlarmOn.short_description = "Change selected projects alarm On"

def AsTemplateCreateNew(self, request, queryset):
    if queryset.count() > 1:self.message_user(request, "Just can selected 1 item, you selected %s items" % queryset.count())
    else:return HttpResponseRedirect("/admin/usetpcreatewidget/%s" % queryset[0].id)
AsTemplateCreateNew.short_description = "Use selected as template create widget"

def ChangeWidgets(self, request, queryset):
    return HttpResponseRedirect("/admin/changewidgets/?wid=%s" % ",".join([str(i.id) for i in queryset]))
ChangeWidgets.short_description = "Change selected widgets"

class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title', 'sequence')
    ordering = ('title',)

class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'rrd', 'category')
    search_fields = ('title','server__ip' )
    ordering = ('title',)
    actions = [ChangeWidgets,AsTemplateCreateNew]

class RrdAdmin(admin.ModelAdmin):
    list_display = ('name', 'des')
    search_fields = ('name', )
    ordering = ('name',)
    actions = ['delete_selected_rrds']
    
    def save_model(self, request, obj, form, change):
        obj.save()
        start_time = '2010-06-01 00:00'
        start_time = time.strptime(start_time, "%Y-%m-%d %H:%M")
        start_time = int(time.mktime(start_time))
        cmd = 'rrdtool create %s --start %d %s' % (settings.RRD_PATH + obj.name + ".rrd", start_time, obj.setting.replace("\n", "").replace("\r", " "))
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
    
    def delete_model(self,request,obj):
        cmd = 'rm %s.rrd' % (settings.RRD_PATH + obj.name)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        obj.delete()
    
    def get_actions(self, request):
        actions = super(RrdAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def delete_selected_rrds(self, request, queryset):
        for obj in queryset:
            cmd = 'rm %s.rrd' % (settings.RRD_PATH + obj.name)
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            obj.delete()
    delete_selected_rrds.short_description = 'Delete selected rrds'

class AlarmLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget', 'created_on','alarmmode')
    ordering = ('-created_on',)

class AlarmAdmin(admin.ModelAdmin):
    list_display = ('title', 'enable')
    ordering = ('title',)

class FrequentAlarmAdmin(admin.ModelAdmin):
    list_display = ('title', 'enable')
    ordering = ('title',)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'alarm', 'sequence')
    ordering = ('name',)
    actions = [projectChangeAlarmOff,projectChangeAlarmOn]

class ServicesTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    ordering = ('name',)

class ServerServerForm(ModelForm):
    class Meta:
        model = Server
        widgets = {
            'password': PasswordInput(),
        }

class ServerServerAdmin(admin.ModelAdmin):
    form = ServerServerForm
    list_display = ('uid', 'name', 'ip', 'physical_server_ip', 'idc', 'projects')
    search_fields = ('ip','name','uid','physical_server_ip' )
    ordering = ('name',)

class StatisticsDayAdmin(admin.ModelAdmin):
    list_display = ('widget', 'date')
    ordering = ('-date',)

class WidgetServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("show_name",)
    ordering = ('name',)

admin.site.register(Server,ServerServerAdmin)
admin.site.register(CmdLog)
admin.site.register(Cmd)
admin.site.register(Rrd, RrdAdmin)
admin.site.register(Dashboard,DashboardAdmin)
admin.site.register(WidgetCategory)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(SeverCmd)
admin.site.register(AlarmServerCmd)
admin.site.register(AlarmUser)
admin.site.register(Alarm, AlarmAdmin)
admin.site.register(AlarmLog, AlarmLogAdmin)
admin.site.register(GraphAider)
admin.site.register(GraphAiderDef)
#admin.site.register(FrequentAlarm,FrequentAlarmAdmin)
#admin.site.register(FrequentAlarmLog)
admin.site.register(DashboardError)
admin.site.register(Project, ProjectAdmin)
admin.site.register(IDC)
admin.site.register(ServiceType,ServicesTypeAdmin)
admin.site.register(WidgetServiceType,WidgetServiceTypeAdmin)
admin.site.register(WidgetGrade)
admin.site.register(StatisticsDay,StatisticsDayAdmin)
admin.site.register(Ticket)
admin.site.register(TicketAction)
admin.site.register(TicketHistory)
admin.site.register(AlarmTest)
admin.site.register(WidgetCategoryTemplate)
admin.site.register(DisableAlarmLog)
