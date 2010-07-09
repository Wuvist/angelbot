from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.conch.telnet import TelnetTransport, TelnetProtocol

class TelnetPrinter(TelnetProtocol):
    def __init__(self):
        self.logined = False
        self.data = ""
        self.current_cmd = ""
        
    def set_cmd(self, cmd):
        self.cmd = cmd
        if type(self.cmd) is str:
            self.cmd = [self.cmd]
        self.cmd.reverse()

    def next_cmd(self):
        if len(self.cmd) == 0:
            self.transport.loseConnection()
            self.factory.end_cb()
        else:
            self.current_cmd = self.cmd.pop()
            self.transport.write(self.current_cmd + "\n")

    def dataReceived(self, bytes):
        self.data += bytes
        
        if self.logined:
            if self.data.endswith(">"):
                self.factory.cb(self.current_cmd, self.data)
                self.data = ""
                self.next_cmd()
        else:            
            if self.data.endswith("login: "):
                self.transport.write(self.factory.server["username"] + "\n")
                self.data = ""
            if self.data.endswith("password: "):
                self.transport.write(self.factory.server["password"] + "\n")
                self.data = ""
            if self.data.endswith(">"):
                #ensure the output is in utf8
                self.transport.write("chcp 65001\n")
                self.set_cmd(self.factory.cmd)
                self.logined = True
                self.data = ""


class TelnetFactory(ClientFactory):
    def __init__(self, server, cmd, cb, end_cb):
        self.server = server
        self.cmd = cmd
        self.cb = cb
        self.end_cb = end_cb
        
    def buildProtocol(self, addr):
        protocol = TelnetTransport(TelnetPrinter)
        protocol.factory = self
        return protocol

if __name__ == '__main__':
    server = {"host": "192.168.1.13", "type": "windows", "username": "administrator", "password" : "mozat01"}
    def cb(cmd, data):
        print data

    def end_cb():
        reactor.stop()            
    cmds = ["dir", "cd \\", "dir"]
    reactor.connectTCP(server["host"], 23, TelnetFactory(server, cmds, cb, end_cb))
    reactor.run()