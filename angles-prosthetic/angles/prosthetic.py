from __future__ import with_statement

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

import logging
import views
from base_prosthetic import Prosthetic, persist_state

from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from google.appengine.api import files, urlfetch
from angles import models

class Angles(Prosthetic):
  """Needs a docstring."""

  @classmethod
  def time_between_runs(cls):
    # as often as possible
    return 1

  def post_oauth_callback(self):
    return redirect(reverse(views.config, args=[self.token.oauth_key]))

  @persist_state
  def act(self, force=False):
    logging.info("Angles acting.")
    data = self.get("/1/weavr/state/")
    logging.info("My name: %s" % data['weavr'])

    # This is disabled for now so that we don't fill up the blobstore every 10 minutes on live.
    if False:
      image_url = "http://www.hackdiary.com/misc/logo_120.gif"
      fetch_response = urlfetch.fetch(image_url)

      # Create a file
      file_name = files.blobstore.create(mime_type='image/gif')

      # Open the file and write to it
      with files.open(file_name, 'a') as f:
        f.write(fetch_response.content)

      # Finalize the file. Do this before attempting to read it.
      files.finalize(file_name)

      # Get the file's blob key
      blob_key = files.blobstore.get_blob_key(file_name)

      logging.info("Created a blob called %s" % blob_key)

      post = self.post("/1/weavr/post/", {
        "category":"article",
        "title":"Test post",
        "body":"Here's an image from the blobstore that I copied from the internet: <img src=\"http://weavrs-angles.appspot.com/angles/blob/" + str(blob_key) + "/\" />",
        "keywords":"testing"
      })

    self.state = { "name" : data['weavr'] }
    run = models.AnglesRun(weavr_token = self.token)
    run.save()
    return True
