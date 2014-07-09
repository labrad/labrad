# -*- coding: utf-8 -*-

"""
### BEGIN NODE INFO
[info]
name = Emitter Server
version = 1.0
description = 
instancename = EmitterServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
import labrad

class EmitterServer(LabradServer):

    """
    Basic Emitter Server
    """
    name = 'Emitter Server'

    onEvent = Signal(123456, 'signal: emitted signal', 's')
    #This is the Signal to be emitted with ID# 123456 the name for the 
    #client to call is signal__emitted_signal and the labrad type is string

    @setting(1, 'Emit Signal', returns='')
    def emitSignal(self, c):
    #function that will onEvent to send signal to listeners
        self.onEvent('Output!')
        #sends signal

if __name__ == "__main__":
    from labrad import util
    util.runServer(EmitterServer())