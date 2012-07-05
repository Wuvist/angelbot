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

class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'rrd', 'category')
    search_fields = ('title', )
    ordering = ('title',)

class RrdAdmin(admin.ModelAdmin):
    list_display = ('name', 'des')
    search_fields = ('name', )
    ordering = ('name',)

class AlarmLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget', 'created_on')
    ordering = ('-created_on',)

class AlarmAdmin(admin.ModelAdmin):
    list_display = ('title', 'enable')
    ordering = ('title',)

class FrequentAlarmAdmin(admin.ModelAdmin):
    list_display = ('title', 'enable')
    ordering = ('title',)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'alarm')
    ordering = ('name',)

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
    list_display = ('name', 'ip', 'idc')
    search_fields = ('ip','name' )
    ordering = ('name',)

admin.site.register(Server,ServerServerAdmin)
admin.site.register(CmdLog)
admin.site.register(Cmd)
admin.site.register(Rrd, RrdAdmin)
admin.site.register(Dashboard)
admin.site.register(WidgetCategory)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(SeverCmd)
admin.site.register(AlarmUser)
admin.site.register(Alarm, AlarmAdmin)
admin.site.register(AlarmLog, AlarmLogAdmin)
admin.site.register(GraphAider)
admin.site.register(GraphAiderDef)
admin.site.register(FrequentAlarm,FrequentAlarmAdmin)
admin.site.register(FrequentAlarmLog)
admin.site.register(DashboardError)
admin.site.register(Project, ProjectAdmin)
admin.site.register(IDC)
admin.site.register(ServiceType,ServicesTypeAdmin)
admin.site.register(WidgetServiceType)
