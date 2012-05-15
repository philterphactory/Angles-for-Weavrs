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
import urllib
import base64

from slideshow import SlideShow
from pyslideshare.pyslideshare import PyslideshareException

from base import Poller, json

class SlidesharePoller(Poller):


    def __init__(self):
        # renders + data waiting to be processed by slideshare before being posted to blog
        self.processing_renders = [] 

    def after_poll(self):
        for slide_data in self.processing_renders:
            print "Checking previously processed render %r"%slide_data
            try:
                if slide_data['slideshow'].check_status() : # if it is already processed
                    print "slide upload is complete!"
                    if self.auth_call(slide_data["server"], self.complete_url, slide_data['data']):
                        self.processing_renders.remove(slide_data)

            except PyslideshareException, e :
                self.failed(slide_data["server"], slide_data['run'], unicode(e))
                self.processing_renders.remove(slide_data)
            except Exception, e:
                self.complain(server, "error processing %s\n%s"%(e,traceback.format_exc(e)))


    def render(self, server, run):
        for slide_data in self.processing_renders:
            if run["id"] == slide_data["run"]["id"]:
                return False

        print "rendering with data %r" % run
        
        try:
            result = self.render_pdf(server, run)
            if not result:
                return False
            pdf_path, png_path = result
            slideshow, permalink_url = self.upload_pdf(server, pdf_path, run)
            self.upload_png(server, png_path, run)

        except Exception, e: # all other exceptions. log and do not retry. includes AssertionError
            print '%s\n%s' %(e, traceback.format_exc(e))
            return self.failed(server, run, e) # dont try again

        if not permalink_url:
            return self.failed(server, run, "permalink is None")

        data = {
            "run_id": run["id"],
            "permalink_url": permalink_url,
            "keywords" : run['tags'],
            "category" : "article",
        }
        print "recording %s"%data
        self.processing_renders.append({
            'data' : data,
            'run' : run,
            'slideshow': slideshow,
            'server': server,
        } )


    def upload_pdf(self, server, path, run):
        """Upload the rendered pdf to SlideShare"""
        slideshow = SlideShow()
        title = "%s %s" % (run['title'], run['id'])
        tags = ",".join(run['tags'].split(" "))
        result = slideshow.upload(run['slideshare'], path, title, tags)
        try:
            os.remove(path)
        except OSError, e :
            print "can't delete file %s"%e
        return slideshow, result


    def upload_png(self, server, path, run):
        """Upload the rendered png thumbnail to the Prosthetic server"""
        png = open(path).read()
        png_base64 = base64.encodestring(png)[:-1]
        data = urllib.urlencode(dict(thumbnail=png_base64, run_id=run['id']))
        self.auth_call(server, self.upload_thumbnail_url, data)
        try:
            os.remove(path)
        except OSError, e :
            print "can't delete file %s"%e

    def failed(self, server, run, error="") :
        """ tell prosthetic to set this run as failed and store error
        this means that run wont be tried to render again.
        """
        print 'Failing run_id %s: %s'%(run['id'], error)
        data = {
            "run_id":run["id"],
            "error_record" :unicode(error),
        }
        self.auth_call(server, self.failed_url, data)
        return False

if __name__ == '__main__':
    SloganeerPoller().start()
