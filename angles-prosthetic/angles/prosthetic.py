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
import re
import datetime
from base_prosthetic import Prosthetic, persist_state

from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from google.appengine.api import files, urlfetch
from angles import models
try: from django.utils import simplejson as json
except ImportError: import json

one_week = datetime.timedelta(7)

def all_pairs(seq):
    l = len(seq)
    for i in range(l):
        for j in range(i+1, l):
            yield seq[i], seq[j]

def format_datetime(dt):
    """Format the datetime object to a string in Weavrs format"""
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

class Angles(Prosthetic):
  """Needs a docstring."""

  @classmethod
  def time_between_runs(cls):
      # daily
      # return 24*60*60
      return 2*60*60

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

    # make sure the token has its job config data -- if not, make a default one
    if self.token.data is None or not self.token.data:
        self.state = {}
        self.state['job'] = json.dumps({
            "font": { "name": "Arial", "size": 14 },
            "kcoreFilter": { "k" : 3 },
            "colour": { "background": "000000", "outline": "cccccc" },
            "opacity": { "outline": 40, "node": 50, "edge": 10 },
            "thickness": { "edge": 10, "outline": 1 },
            "colourloversPalette": 4182
            })
    else:
        self.state = json.loads(self.token.data)

    self.state['gexf'] = self.load_gexf()

    # check for most-recent palette post and use it to override palette in the job
    colourposts = self.token.get_json("/1/weavr/post", {"category":"palette", "per_page":1})
    if len(colourposts['posts']) == 1:
        url = colourposts['posts'][0]['source_url']
        logging.info("Found a palette source URL: %s" % url)
        colourmatch = re.search('palette/([0-9]+)/', url)
        if colourmatch is not None:
            colour_id = colourmatch.group(1)
            logging.info("Replacing palette in the render job with %s" % colour_id)

            # unfortunately have to un-parse the JSON, modify it then dump it out again
            job = json.loads(self.state['job'])
            job['colourloversPalette'] = colour_id
            self.state['job'] = json.dumps(job)

    run = models.AnglesRun(weavr_token = self.token)
    run.save()
    return True

  def load_gexf(self):
    blacklist = set(['just'])

    runs = [self.token.get_json("/1/weavr/post", {
      'before':format_datetime(datetime.datetime.now() - datetime.timedelta(n)),
      'after':format_datetime(datetime.datetime.now() - datetime.timedelta(n+1)),
      'per_page':50
    }) for n in range(0,7)] # a week, retrieved a day at a time

    node_names = set()
    edges = dict()
    for run in runs:
        for post in run['posts']:
            keywords = list(set(post['keywords'].split()))
            keywords = [keyword for keyword in keywords if keyword.lower() not in blacklist]
            node_names.update(keywords)
            for pair in all_pairs(keywords):
                # Make sure a/b and b/a are counted the same
                edge = tuple(sorted(pair))
                edges[edge] = edges.get(edge, 0) + 1
    nodes = list(node_names)
    logging.info("Made a GEXF graph with %d nodes and %d edges." % (len(nodes), len(edges)))

    # xml dump
    gexf = u''
    gexf += u'<?xml version="1.0" encoding="UTF-8"?>'
    gexf += u'<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">'
    gexf += u'<graph mode="static" defaultedgetype="undirected">'
    gexf += u'<nodes>'
    for node in nodes:
        gexf += u'<node id="%s" label="%s" />' % (node, node)
    gexf += u'</nodes>'
    gexf += u'<edges>'
    edge_id = 0
    for edge, weight in edges.iteritems():
        gexf += u'<edge id="%i" source="%s" target="%s" weight="%f" />'\
            % (edge_id, edge[0], edge[1], weight)
        edge_id += 1
    gexf += u'</edges>'
    gexf += u'</graph>'
    gexf += u'</gexf>'
    return gexf
