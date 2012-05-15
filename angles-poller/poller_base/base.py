#! /usr/bin/python

# Copyright (C) 2011 Philter Phactory Ltd.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE X
# CONSORTIUM BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Except as contained in this notice, the name of Philter Phactory Ltd. shall
# not be used in advertising or otherwise to promote the sale, use or other
# dealings in this Software without prior written authorization from Philter
# Phactory Ltd..
#

import os
import time, datetime
import sys
import traceback
import logging
import base64
import random
import signal

logging.Logger.setLevel( logging.getLogger(), logging.INFO )

# this represents one possible  strategy.
#
# PLAN
#
# * every N seconds, ask server for things that need doing
# * render them
# * post to server when done

import urllib, urllib2
try: import simplejson as json
except ImportError: import json

try :
    # you can store your server url and password into a module  
    from server_settings import PTK_SERVERS, POLL_TIME
except ImportError:
    logging.warn("Can't find PTK_SERVERS or POLL_TIME in server_settings.py - legacy mode")

    try :
        # you can store your server url and password into a module  
        from server_settings import PTK_SERVER
        from server_settings import PTK_PASSWORD
    except ImportError:
        # or you can set them here 
        logging.warn("Can't find server_settings.py at all - assuming development mode")
        PTK_SERVER="localhost:8000"
        PTK_PASSWORD="devdevdev" # MUST match value in Config object on ptk server

    PTK_SERVERS = [ [ PTK_SERVER, PTK_PASSWORD ] ]
    POLL_TIME = 10

try :
    # you can store your server url and password into a module  
    from server_settings import NAME
except ImportError:
    NAME = "unnamed"


class WeavrServer(object):
    def __init__(self, a):
        self.host = a[0]
        self.protocol = "http"
        if "appspot.com" in self.host:
            self.protocol = "https"
        self.password = a[1]
    
    def __unicode__(self):
        return "%s://%s"%( self.protocol, self.host )

class Poller(object):
    
    # default poller
    def poll(self, server):
        data = self.auth_call(server, self.pending_url)
        if not data:
            return False
    
        pending = json.loads(data)
        if not pending:
            return False
    
        for run in pending:
            track = self.render(server, run)
    
        return True
    
    def after_poll(self):
        return False

    def auth_call(self, server, path, data=None):
        try:
            if isinstance(data, dict):
                data = urllib.urlencode(data)
            req = urllib2.Request("%s://%s%s"%(server.protocol, server.host, path), data)
            base64string = base64.encodestring('%s:%s'%("user", server.password))[:-1]
            req.add_header("Authorization", "Basic %s"%base64string)
            response = urllib2.urlopen(req)
            return response.read()
        except urllib2.HTTPError, e:
            logging.error("Can't call %s on %s: %s"%(path, server, e))
            return None


    def complain(self, server, error):
        # TODO - the plan here is to post a message to the ptk server
        # explaining that we had a problem trying to render this object.
        logging.error("there was an error talking to %s: %s"%(server, error))
        #raise Exception(error)

    
    def start(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print "******* %s starting up @ %s *******" %(self.__class__.__name__, now)

        class TimeoutException(Exception):
            pass

        def timeout(signum, frame):
            # call took too long.
            raise TimeoutException("call took too long. timing out.")

        servers = map(WeavrServer, PTK_SERVERS)

        while True:
            did_something = False

            # in case one of them is _really_ broken, we'll shuffle every run so everonye
            # gets a chance to be first.
            random.shuffle(servers)
    
            for server in servers:
                logging.info("%s polling %s"%(self.__class__.__name__, server.host))
                signal.signal(signal.SIGALRM, timeout)
                try:
                    signal.alarm(60)
                    did_something = self.poll(server)
                except Exception, e:
                    signal.alarm(0)
                    self.complain(server, "error polling %s: %s\n%s"%(server.host, e,traceback.format_exc(e)))
                    # wait longer if there was a problem, so we don't destroy the server
                    time.sleep(20)
                signal.alarm(0)
            
            self.after_poll()


            # ping phloor to tell it about this mediasynth
            phloor_server = "http://phloor.weavrs.com/ping/"
    
            try:
                from deploy_data import data
            except ImportError:
                data = dict(revision="",shipped="", version="")
    
            payload=dict(
                name="%s (%s)"%( self.__class__.__name__, NAME ),
                type="mediasynth",
                url="http://www.weavrs.com/",
                deployed_at=data["shipped"],
                revision=data["revision"],
            )
            try:
                req = urllib2.Request(phloor_server, urllib.urlencode(payload))
                urllib2.urlopen(req)
            except Exception, e:
                logging.warn("can't ping phloor: %s"%e)

            time.sleep(POLL_TIME)

