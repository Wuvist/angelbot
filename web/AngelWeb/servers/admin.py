#!/usr/bin/env python
# encoding: utf-8
"""
admin.py

Created by Wuvist on 2010-07-01.
Copyright (c) 2010 . All rights reserved.
"""

from django.contrib import admin
from AngelWeb.servers.models import *


admin.site.register(Server)
admin.site.register(CmdLog)
admin.site.register(Cmd)
admin.site.register(Rrd)
admin.site.register(Dashboard)
admin.site.register(Widget)
admin.site.register(SeverCmd)
admin.site.register(AlarmUser)
admin.site.register(Alarm)
admin.site.register(AlarmLog)
admin.site.register(GraphAider)
admin.site.register(GraphAiderDef)