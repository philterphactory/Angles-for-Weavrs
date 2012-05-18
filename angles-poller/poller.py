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
import traceback
import logging
import urllib2
from poller_base import Poller
try: from django.utils import simplejson as json
except ImportError: import json

class AnglesPoller(Poller):
    
    def __init__(self):
        self.pending_url = "/angles/pending/"

    def render(self, server, run):

        id = run['run_id']

        try:
            return self.safe_render(server, run)
        except Exception, e:
            logging.warn("Failing : %s\n%s"%(e, traceback.format_exc(e)))
            data = {
                "run_id":id,
                "error_record" :unicode(e)
            }
            self.auth_call(server, "/angles/failed/", data)
            return False


    def safe_render(self, server ,run):
        print "rendering on server %s with data %r" % (server,run)

        # kind of crude but just in case ...
        try :
            instance_name = run["instance_name"]
        except KeyError :
            print "WARNING : no server instance_name received, defaulting..."
            instance_name = 'weavrs-angles' # default

        if instance_name == '' :
            instance_name = 'weavrs-angles' # default

        data = json.loads(run['data'])

        id = run['run_id']

        print "Making a PNG for run %d" % id
        gexf = open("/tmp/render.gexf","w")
        gexf.write(data['gexf'])
        gexf.close()
        job_json = json.loads(data['job'])
        job_json['input'] = '/tmp/render.gexf'
        job_json['output'] = '/tmp/render.png'
        job = open("/tmp/render.json","w")
        job.write(json.dumps(job_json))
        job.close()
        os.system("java -cp ../angles-gephi/build/:lib/gephi-toolkit.jar:lib/jackson-annotations-2.0.1.jar:lib/jackson-core-2.0.1.jar:lib/jackson-databind-2.0.1.jar com.weavrs.gephi.Main /tmp/render.json")

        data = {
            "run_id": id,
            "success": True,
            "message": "Keyword interactions for this week.",
            "image1": open("/tmp/render.png","rb")
        }
        print "posting %s"%data
        response = self.auth_call_with_files(server, "/angles/complete/", data)
        print "posted %s"%data
        return True

if __name__ == '__main__':
    AnglesPoller().start()
