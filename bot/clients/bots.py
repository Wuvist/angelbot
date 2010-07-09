#!/usr/bin/env python
# encoding: utf-8
"""
bots.py

Created by Wuvist on 2010-06-27.
Copyright (c) 2010 . All rights reserved.
"""
from twisted.internet import reactor, protocol, defer
import telnet, ssh
bots = {}

class bot:
    def __init__ (self, server):
        self.server = server
        self.is_logined = False
        bots[server] = self
        if self.server["type"] == "ssh":
            self.client = telnet.client()
        else:
            self.client = ssh.client()

    def on_logined(self):
        self.is_logined = True

    def batch (self, cmds):
        for cmd in cmds.split("\n"):
            self.tn.write(cmd + "\r\n")
            print self.tn.read_until(">")
        
    def logout (self):
        self.tn.write("exit\r\n")
        print self.tn.read_all()
        print "logouted. Press enter to close window"
