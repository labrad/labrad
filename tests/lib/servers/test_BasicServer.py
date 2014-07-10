# -*- coding: utf-8 -*-

from twisted.trial.unittest import TestCase

import labrad

class Test_BasicServer(TestCase):
    """
    Test Basic Server
    """

    
    def setUp(self):
        """
        Connect to labrad
        """
        self.cxn = labrad.connect() #host='localhost')

    
    def tearDown(self):
        """
        Disconnect from labrad
        """
        self.cxn.disconnect()


    def _get_tester(self):
        """
        Connect to BasicServer
        """
        self.assert_(hasattr(self.cxn, 'basic_server'))
        return self.cxn.basic_server


    def test_BasicServerInServers(self):
        """
        Test that BasicServer is in servers
        """
        servers = self.cxn.servers
        self.assert_('basic_server' in servers)


#        self.assert_(len(servers.keys()) > 0)
#        self.assert_('manager' in servers)

#        self._get_manager()
#        self._get_tester()
#        
#        self._get_manager()
#        self._get_tester()


    def test_AreThereServers(self):
        """
        Test that there are servers
        """
        servers = self.cxn.servers
        self.assert_(len(servers.keys()) > 0)        


    def test_echo(self):
        """
        Test that server has basic function echo
        """
        
        pts = self._get_tester()

        # make sure we can access the setting by both allowed methods
        self.assert_(hasattr(pts, 'echo'))


    def test_faux_echoExists(self):
        """
        Test that server has function  faux_echo
        """
        
        pts = self._get_tester()

        # make sure we can access the setting by both allowed methods
        self.assert_(hasattr(pts, 'faux_echo'))
                

    def test_faux_echoResponse(self):
        """
        Test that fuax_echo responds appropriately
        """
        pts = self._get_tester()                        
        
        # single setting, named explicitly
        resp = pts.faux_echo('faux_echo string test')
        self.assertEquals(resp, 'faux_echo string test')

#        resp = pts.echo(T.Value(15.0, 's'))
#        self.assertEquals(float(resp), 15.0)
#        self.assertEquals(resp.unit.name, 's')
    
    
#    def test_fauxEcho(self):
#        """
#        """
#        return string



#
#class PoetryTestCase(TestCase):
#
#    def setUp(self):
#        factory = PoetryServerFactory(TEST_POEM)
#        from twisted.internet import reactor
#        self.port = reactor.listenTCP(0, factory, interface="127.0.0.1")
#        self.portnum = self.port.getHost().port
#
#    def tearDown(self):
#        port, self.port = self.port, None
#        return port.stopListening()
#
#    def test_client(self):
#        """The correct poem is returned by get_poetry."""
#        d = get_poetry('127.0.0.1', self.portnum)
#
#        def got_poem(poem):
#            self.assertEquals(poem, TEST_POEM)
#
#        d.addCallback(got_poem)
#
#        return d
#
#    def test_failure(self):
#        """The correct failure is returned by get_poetry when
#        connecting to a port with no server."""
#        d = get_poetry('127.0.0.1', 0)
#        return self.assertFailure(d, ConnectError)




