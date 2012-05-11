from __future__ import with_statement # Note this MUST go at the top of your views.py

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

from django.http import HttpResponse, HttpResponseNotFound
from google.appengine.ext import blobstore
from django import http
from django.utils.http import http_date
import time

def test(request):
    """ Quick test to make sure content is coming back correctly. """

    return HttpResponse('{"message":"seems to be working and mattb can deploy"}', mimetype="application/json")

# http://blainegarrett.com/2011/04/02/appengine-files-api-part-1-storingfetching-remote-images-in-blobstore-using-django/
def blob(request, blob_key):
  blob_info = blobstore.BlobInfo.get(blob_key)
  if not blob_info:
    raise Exception('Blob Key does not exist')

  blob_file_size = blob_info.size
  blob_content_type = blob_info.content_type

  # Attempt to fetch the blob in one or more chunks depending on size and api limits
  blob_concat = ""
  start = 0
  end = blobstore.MAX_BLOB_FETCH_SIZE - 1
  step = blobstore.MAX_BLOB_FETCH_SIZE - 1

  while(start < blob_file_size):
    blob_concat += blobstore.fetch_data(blob_key, start, end)
    temp_end = end
    start = temp_end + 1
    end = temp_end + step

  response = http.HttpResponse(blob_concat, mimetype=blob_content_type)
  response['Expires'] = http_date(time.time() + 24 * 60 * 60 * 365)
  return response
