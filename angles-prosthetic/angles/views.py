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
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from webapp.models import AccessToken
from google.appengine.api import files, urlfetch
from google.appengine.ext import blobstore
from google.appengine.runtime import DeadlineExceededError
from django import http
from django.utils.http import http_date
import traceback
import time, datetime
import models
import forms
import logging
try: from django.utils import simplejson as json
except ImportError: import json
from webapp.client import OAuthForbiddenException, OAuthUnauthorizedException

def test(request):
  """ Quick test to make sure content is coming back correctly. """

  return HttpResponse('{"message":"seems to be working and mattb can deploy"}', mimetype="application/json")

def config(request, weavr_token):
  token = get_object_or_404(AccessToken, oauth_key=weavr_token)    

  # add the default
  if token.data is None or not token.data:
      token.data = json.dumps({"job": json.dumps({
          "font": { "name": "Arial", "size": 14 },
          "kcoreFilter": { "k" : 3 },
          "colour": { "background": "000000", "outline": "cccccc" },
          "opacity": { "outline": 40, "node": 50, "edge": 10 },
          "thickness": { "edge": 10, "outline": 1 },
          "colourloversPalette": 4182
          })})
      token.save()

  current_config = json.loads(token.data)
  current_job = json.loads(current_config['job'])
  
  if request.method == 'POST':
    form = forms.ConfigForm(request.POST)
    if form.is_valid():
      current_job['kcoreFilter']['k'] = form.cleaned_data['kcore']
      current_job['colour']['background'] = form.cleaned_data['background_colour'].lower()
      current_job['font']['name'] = form.cleaned_data['font_name']
      current_job['font']['size'] = form.cleaned_data['font_size']
      if form.cleaned_data['colourlovers_palette_id']:
          current_job['colourloversPalette'] = form.cleaned_data['colourlovers_palette_id']
      else:
          if current_job.has_key('colourloversPalette'):
              del current_job['colourloversPalette']

      current_config['job'] = json.dumps(current_job)
      token.data = json.dumps(current_config)
      token.save()
      return http.HttpResponseRedirect('/angles/config/%s/' % weavr_token)
  else:
    formdata = {
        'background_colour': current_job['colour']['background'],
        'kcore': current_job['kcoreFilter']['k'],
        'font_name': current_job['font']['name'],
        'font_size': current_job['font']['size'],
    }
    if current_job.has_key('colourloversPalette'):
        formdata['colourlovers_palette_id'] = current_job['colourloversPalette']
    form = forms.ConfigForm(formdata)

  return render_to_response("config.html", locals(),
    context_instance=RequestContext(request))

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

  while start < blob_file_size:
    blob_concat += blobstore.fetch_data(blob_key, start, end)
    temp_end = end
    start = temp_end + 1
    end = temp_end + step

  response = http.HttpResponse(blob_concat, mimetype=blob_content_type)
  response['Expires'] = http_date(time.time() + 24 * 60 * 60 * 365)
  return response

def pending(request):
    """ returns json with data for angles."""
    try :
        config = models.config()
    except DeadlineExceededError, e :
        logging.warning( '%s error getting whistler_config' % e)
        logging.warning( traceback.format_exc() )
        return None

    response = authenticate(request, config)
    if response: return response

    # generate the output
    output = json.dumps([{ 
        "instance_name" : "x",
        "run_id" : x.id,
        "data" : x.weavr_token.data
        } for x in models.AnglesRun.objects.filter(completed__isnull=True)])

    return HttpResponse(output, content_type="application/json")

    
    return HttpResponse(blob_key, content_type="text/plain")

def pending_flush(request):
    """ empties the pending queue without doing anything about the jobs. for debug use. """
    try :
        config = models.config()
    except DeadlineExceededError, e :
        logging.warning( '%s error getting whistler_config' % e)
        logging.warning( traceback.format_exc() )
        return None

    response = authenticate(request, config)
    if response: return response

    deletable = models.AnglesRun.objects.filter(completed__isnull=True)
    logging.error('pending_flush: %s deletables' % len(deletable))
    count = len([x.delete() for x in deletables])
    return HttpResponse("OK: %d deleted." % count, content_type="text/plain")

def complete(request):
    """ called from poller on sucessful run."""
    config = models.config()
    response = authenticate(request, config)
    if response: return response

    run_id = request.POST.get("run_id")

    run = get_object_or_404(models.AnglesRun, id=run_id)

    try :
        run.completed = datetime.datetime.utcnow()

        # make a post per uploaded file
        for key,infile in request.FILES.items():
            file_name = files.blobstore.create(mime_type='image/png')
            with files.open(file_name, 'a') as f:
              f.write(infile.read())
            files.finalize(file_name)
            blob_key = files.blobstore.get_blob_key(file_name)
            logging.info("Uploaded a file to blob_key %s" % blob_key)

            logging.info("Making a blog post on %s" % run.weavr_token.weavr_url)
            post = run.weavr_token.post("/1/weavr/post/", {
                "category":"article",
                "title": request.POST.get("message"),
                "keywords": "Angles",
                "body" : "<img src='http://weavrs-angles.appspot.com/angles/blob/%s/'>" % blob_key
            })
            run.post_id = post["post_id"]

        run.success = True
        run.error_record = None
        run.save()
    except OAuthForbiddenException, e :
        logging.info( '%s error posting to weavr' % e)
        logging.info( traceback.format_exc() )

        run.success = False
        run.error_record = '%s error posting to weavr' % e
        run.save()
    except OAuthUnauthorizedException, e :
        logging.info( '%s error posting to weavr' % e)
        logging.info( traceback.format_exc() )
        
        run.success = False
        run.error_record = '%s error posting to weavr' % e
        run.save()
    except DeadlineExceededError, e :
        logging.warning( '%s error posting to weavr' % e)
        logging.warning( traceback.format_exc() )


    output = json.dumps({ "post_id":run.post_id }, indent = 4)
    return HttpResponse(output, content_type="text/plain")


def failed(request) :
    run_id = request.POST.get("run_id")
    error_record = request.POST.get("error_record")

    logging.warning('Run %s FAILED . %s' % (run_id, error_record))

    run = get_object_or_404(models.AnglesRun, id=run_id)
    run.completed = datetime.datetime.utcnow()
    run.success = False
    run.error_record = error_record
    run.save()

    output = json.dumps({ "run_id":run_id }, indent = 4)
    return HttpResponse(output, content_type="text/plain")

def basic_challenge():
    # TODO: Make a nice template for a 401 message?
    realm = "weavrs angles"
    response =  HttpResponse('Authorization Required\n', mimetype="text/plain")
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    response.status_code = 401
    return response

def basic_authenticate(authentication):
    (authmeth, auth) = authentication.split(' ',1)
    if 'basic' != authmeth.lower():
        return None
    auth = auth.strip().decode('base64')
    return auth.split(':',1)

def authenticate(request, config):
    if not request.META.has_key('HTTP_AUTHORIZATION'):
        return basic_challenge()
    username, password = basic_authenticate(request.META['HTTP_AUTHORIZATION'])
    wanted = config.server_password
    if password != wanted:
        return basic_challenge()
    return None
