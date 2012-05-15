# -*- coding: utf-8 -*-
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

"""Slideshow client library

Utility class for uploading things into Slideshow

Usage:
    
"""


import os, sys, time, logging
import urllib2, urllib
import traceback
import time
from pyslideshare.pyslideshare import pyslideshare, PyslideshareException


class SlideShow(object):

    api = None

    def __init__(self) :
        self.slideID = None

    def already_uploaded(self, title, username) :
        """ checks if a slide with the given title and given username has already been uploaded
            if so returns the permalink
        """
        try :
            json = SlideShow.api.get_slideshow_by_user(username_for=username, get_unconverted=True)
        except urllib2.HTTPError, e :
            print e
            return False
        
        count  = int(json['User']['count']['value'])
        
        if count == 0 :
            print 'NO SLIDES in that account yet'
            return False

        show = json['User']['Slideshow']
        
        if count == 1 : # if only one slide it does not come inside a list
            print 'ONLY ONE slide in that account'
            show = [show]

        for sl in show :
            if sl['Title']['value'] == title :
                return sl['Permalink']['value']

        return False # not there

    
    def done_processing(self, url) :
        ''' true if we can access the url
        '''
        url_opener = urllib.URLopener()
        new_url = ''
        try:
            data = url_opener.open(url)
            return True
        except IOError, e: 
            return False


    def check_status(self): 

        if self.slideID is None :
            print 'warning slideID is None!'
            return False
        
        sls = SlideShow.api.get_slideshow(slideshow_id=self.slideID)
        status = int(sls['Slideshow']['Status']['value'])

        print 'slideshare processing status for slide %s is %s' % (self.slideID, status)
        if status < 2 :
            return False #None # not processed yet. keep trying
        elif status == 2 :
            if self.done_processing(sls['Slideshow']['URL']['value']) :
                return True
            else:
                waiting = time.time() - self.upload_time
                if waiting < 3600 * 2:
                    print 'Slideshare api says it is processed but we cannot access the permalink (waited %s seconds so far). Waiting.'%waiting
                    return False
                else:
                    print 'Slideshare api says it is processed but we cannot access the permalink. Giving up.'
                    raise PyslideshareException('giving up after %s seconds'%waiting)

        else :
            raise PyslideshareException('slide file not processed properly')


    def upload(self, auth_data, path, title, tags='', description='', cc_license='') :
        url = ''

        username = auth_data['username']
        password = auth_data['password']

        # the APP AUTH data needs to be in local variables to be passed with locals()
        if not SlideShow.api :
            api_key = auth_data['api_key']
            secret_key = auth_data['secret_key']
            SlideShow.api = pyslideshare(locals(), verbose=False) #, proxy=proxy)

        permalink = self.already_uploaded(title, username)
        if permalink :
            print 'file already uploaded, url permalink is %s' % permalink
            # BUT we MUST find out the slide ID from the permalink to be able to check for processing status
            sls = SlideShow.api.get_slideshow(slideshow_url=permalink)
            self.slideID = sls['Slideshow']['ID']['value'] # we need to set this for check_status()
            return permalink
            
        self.upload_time = time.time()

        new_sls = SlideShow.api.upload_slideshow(
                            slideshow_title = title,
                            slideshow_description = description,
                            
                            slideshow_tags = tags,
                            slideshow_srcfile = path,
                            
                            username = username,
                            password = password,
                            
                            make_src_public = 'Y',
                            make_slideshow_private = 'N',
                            generate_secret_url = 'N',
                            allow_embeds = 'Y',
                            share_with_contacts = 'Y'
                        )
        
        print 'uploading to slideshare %s' %  path
        
        self.slideID = new_sls.SlideShowUploaded.SlideShowID # need this to check later if has been processed
        
        print 'slideID is %s' % self.slideID

        slide = SlideShow.api.get_slideshow(slideshow_id=self.slideID)
        url = slide['Slideshow']['URL']['value']

        print 'url permalink is %s' % url
            
        return url


class SlideshareUpload(object):

    def __init__(self, path, auth_data, cc_license, tags, description, title):
        self.path = path
        self.auth_data = auth_data
        self.tags = tags
        self.description = description
        self.title = title

    def upload(self) :
        self.slideshow = SlideShow() # store it to check if has been processed
        result = self.slideshow.upload(self.auth_data,
                                       path,
                                       self.title,
                                       self.tags,
                                       self.description,
                                       self.cc_license)
        try:
            os.remove(self.path)
        except OSError, e :
            print "can't delete file %s"%e
        return result

