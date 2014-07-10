# -*- coding: utf-8 -*-

"""
### BEGIN NODE INFO
[info]
name = Basic Server
version = 1.0
description = 
instancename = BasicServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting

class BasicServer(LabradServer):
    """
    Basic Server
    """
    
    name = 'Basic Server'



    @setting(1, 'faux_echo', string='s', returns='s')
    def fauxEcho(self, c, string):
        """
        """
        return string

if __name__ == "__main__":
    from labrad import util
    util.runServer(BasicServer())