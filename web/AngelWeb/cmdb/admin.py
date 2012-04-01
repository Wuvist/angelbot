#!/usr/bin/env python
# encoding: utf-8

from AngelWeb.cmdb.models import *
from django.contrib import admin

class ServerAdmin(admin.ModelAdmin):
    list_display = ('ip', 'name', 'available')
    
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'ip', 'service_type', 'available')
    

admin.site.register(Server,ServerAdmin)
admin.site.register(Service,ServiceAdmin)
