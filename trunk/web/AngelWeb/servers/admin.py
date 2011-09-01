#!/usr/bin/env python
# encoding: utf-8
"""
admin.py

Created by Wuvist on 2010-07-01.
Copyright (c) 2010 . All rights reserved.
"""

from django.contrib import admin
from AngelWeb.servers.models import *

class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'rrd', 'category')
    ordering = ('title',)

class RrdAdmin(admin.ModelAdmin):
    list_display = ('name', 'des')
    ordering = ('name',)

class AlarmLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget', 'created_on')
    ordering = ('-created_on',)

class AlarmAdmin(admin.ModelAdmin):
    list_display = ('title', 'enable')
    ordering = ('title',)

admin.site.register(Server)
admin.site.register(CmdLog)
admin.site.register(Cmd)
admin.site.register(Rrd, RrdAdmin)
admin.site.register(Dashboard)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(SeverCmd)
admin.site.register(AlarmUser)
admin.site.register(Alarm, AlarmAdmin)
admin.site.register(AlarmLog, AlarmLogAdmin)
admin.site.register(GraphAider)
admin.site.register(GraphAiderDef)