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


from django.db import models
try: from django.utils import simplejson as json
except ImportError: import json

from webapp.models import AccessToken


class AnglesRun(models.Model):
    # the weavr we're associated with
    weavr_token = models.ForeignKey(AccessToken)

    # when was this created / requested?
    created = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)

    # when was this whistle completed. null means 'not yet'
    completed = models.DateTimeField(null=True)

    # where is the content uploaded to
    source_url = models.CharField(max_length=255,null=True,blank=True)

    title = models.CharField(max_length=255, blank=False)
    description = models.CharField(max_length=255, blank=False)
    keywords = models.CharField(max_length=255, blank=False)

    post_id = models.CharField(max_length=255, blank=False)


    success  = models.NullBooleanField(null=True) # null whencreated

    # details about the reason for the failure to render/upload or post
    error_record = models.CharField(max_length=255, null=True)

    bot_name = models.CharField(max_length=255, blank=False)

class AnglesConfig(models.Model):

    server_password = models.CharField(max_length=255, blank=False, help_text="shared password with the whistler server")
    instance_name = models.CharField(max_length=255, blank=False, help_text="the name of the instance", default="weavrs-angles")
    title = models.CharField(max_length=255, blank=False, help_text="Title for the WP posts, gets appended the keywords used")

def config():
    try:
        return AnglesConfig.objects.all()[0]
    except IndexError:
        raise Exception("No Config object defined")
