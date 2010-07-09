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
from servers.models import Server

@login_required()
def home(request):
    win_servers = Server.objects.filter(server_type="W").all()
    linux_servers = Server.objects.filter(server_type="L").all()    

    c = RequestContext(request, 
        {"win_servers":win_servers, 
        "linux_servers": linux_servers
        })
    return render_to_response('home.html',c)