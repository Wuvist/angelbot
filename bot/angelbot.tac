#!/usr/bin/env python
# encoding: utf-8
"""
angelbot.py

Created by Wuvist on 2010-06-27.
Copyright (c) 2010 __MyCompanyName__. All rights reserved.
"""

from twisted.web.resource import Resource
from twisted.web import server, resource
from twisted.internet import defer, protocol, reactor
from clients import ssh, telnet
from twisted.application import service, internet
from hosts import logins

RRD_PATH = '../rrds/'

class MyResource(Resource):
    def render_GET(self, request):
        return "<html>Hello, world!</html>"

class Foo(Resource):
    def render_GET(self, request):
        server_name = request.args["server"][0]
        cmd = request.args["cmd"]
        server_info = logins[server_name]
        
        def cb(cmd, data):
            request.setHeader("content-type", "text/plain")
            request.write(data)
            
        def end_cb():
            request.finish()    
        if server_info["type"] == "linux":
            protocol.ClientCreator(reactor, ssh.SimpleTransport, server_info, cmd[0], cb, end_cb).connectTCP(server_info["host"], 22)
        else:
            reactor.connectTCP(server_info["host"], 23, telnet.TelnetFactory(server_info, cmd, cb, end_cb))
        return server.NOT_DONE_YET



class rrd(Resource):
    def render_GET(self, request):
        
        def current_rounded_time():
            import time
            timestamp = int(time.time())
            reminder = timestamp % 60
            timestamp = timestamp - reminder
            if reminder > 30:
                timestamp = timestamp + 60
            return timestamp
            
        rrd = request.args["rrd"][0] + ".rrd"
        value = ":".join(request.args["v"])

        import rrdtool
        try:
            rrdtool.update(RRD_PATH + rrd , '%d:%s' % (current_rounded_time(), value))
        except:
            return "Err"
        return "OK"
        

root = MyResource()
root.putChild("foo", Foo())
root.putChild("rrd", rrd())
source = root
application = service.Application("AngelBot")

sc = service.IServiceCollection(application)
site = server.Site(root)
i = internet.TCPServer(8080, site)
i.setServiceParent(sc)