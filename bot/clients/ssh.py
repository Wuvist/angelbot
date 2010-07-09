#!/usr/bin/env python
# encoding: utf-8
"""
ssh.py

Created by Wuvist on 2010-06-27.
Copyright (c) 2010 . All rights reserved.
"""

from twisted.conch.ssh import transport, userauth, connection, common, keys, channel
from twisted.internet import defer, protocol, reactor
from twisted.python import log
import struct, sys, getpass, os



class SimpleTransport(transport.SSHClientTransport):
    def __init__(self, server, cmd, cb, end_cb):
        self.server = server
        self.cmd = cmd
        self.cb = cb
        self.end_cb = end_cb
        
    def verifyHostKey(self, hostKey, fingerprint):
        #print 'host key fingerprint: %s' % fingerprint
        return defer.succeed(1) 

    def connectionSecure(self):
        authService = SimpleUserAuth(self.server["username"], SimpleConnection())
        self.requestService(authService)

class SimpleUserAuth(userauth.SSHUserAuthClient):
    def serviceStarted(self):
        self.authenticatedWith = []
        self.triedPublicKeys = []
        self.lastPublicKey = None
        self._cbPassword(self.transport.server["password"])
            

class SimpleConnection(connection.SSHConnection):
    def serviceStarted(self):
        self.openChannel(CatChannel(2**16, 2**15, self))

class CatChannel(channel.SSHChannel):
    name = 'session'

    def openFailed(self, reason):
        print 'echo failed', reason

    def channelOpen(self, ignoredData):
        self.data = ''
        d = self.conn.sendRequest(self, 'exec', common.NS(self.conn.transport.cmd), wantReply = 1)
        d.addCallback(self._cbRequest)

    def _cbRequest(self, ignored):
        self.conn.sendEOF(self)

    def dataReceived(self, data):
        self.data += data

    def closed(self):
        self.conn.transport.cb(self.conn.transport.cmd, self.data)
        self.loseConnection()
        self.conn.transport.end_cb()
        
def main():
    server = {"host": "192.168.1.12", "type": "linux", "username": "mozat", "password" : "mozat"}
    def cb(data):
        print data
    protocol.ClientCreator(reactor, SimpleTransport, server, "ls", cb).connectTCP(server["host"], 22)
    reactor.run()

if __name__ == '__main__':
    main()
