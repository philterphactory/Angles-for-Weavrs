Development experience creating a media-producing prosthetic for Weavrs
=======================================================================

*Author: Matt Biddulph*

*June 2012*

In two weeks in May 2012 I created the code in [Angles For
Weavrs](https://github.com/philterphactory/Angles-for-Weavrs). It's a
mixture of Python/Django and Java code that creates a graph
visualisation of a Weavr's keyword usage over the preceding week. This
document records the process of creating the code.

Architecture and software components
------------------------------------

The components of the system are:

1. Prosthetic web interface (Python using Django on Google Appengine)
2. Prosthetic job poller (Python)
3. Commandline graph-visualisation renderer (Java using Gephi)

The web interface is used to add the prosthetic to an individual Weavr
via the usual OAuth flow. After a Weavr has been authenticated and the
tokens added to the prosthetic's Appengine database, a configuration
screen is shown where the user can customise some parameters of the
visualisation. The PTK uses Appengine's cron mechanism to call the *act*
method of the Angles prosthetic class to be called on a regular basis
(once per day by default) so that it can generate a run of the
visualiser. This method uses the oauth tokens supplied by the PTK to
retrieve data required for the visualisation (GEXF-format keyword data,
latest Colourlovers palette if the Weavr has one, and config settings)
and stores it using the PTK's *@persist_state* mechanism. It then
creates an instance of AnglesRun, a database object representing the
need to run the visualiser.

The visualiser is a commandline tool that accepts one or more job
definitions in JSON format and outputs a PNG. The JSON contains
rendering parameters (e.g. opacity and colour palette) as well as
embedded graph data in GEXF XML format.

Because the Java/Gephi visualiser requires Java features that are banned
on Appengine (e.g. java AWT graphics toolkit), it's necessary to run it
on a server elsewhere. This is why we need a separate job poller to
coordinate the runs. The poller frequently checks a fixed *pending* URL
on the web interface for a list of jobs to be run. The URL is protected
by HTTP Basic Authentication - no OAuth is involved between the poller
and the web interface, and the poller never talks to the Weavrs API.
This URL returns a list of job data in JSON format by checking for
AnglesRun objects whose *completed* flag is False and dumping the
associated state data (that was previously computed in the PTK's cron)
for each job. The poller then execs the visualiser once per job, and
makes an HTTP POST back to the web interface to complete the job (a
separate failure URL is used in the case of something going wrong). This
POST uses form-multipart encoding to embed the PNG data.

The handler for the multipart HTTP POST in the web interface does
several jobs. Firstly it checks that the identifier supplied matches an
actual AnglesRun, rejecting the POST if not. Then it updates the
AnglesRun object to mark it as completed. It stores the PNG using the
Appengine *blobstore* mechanism for serving large files, and notes the
generated URL. Then it calls the */1/weavr/post* API to create a
blogpost for the intended Weavr, directly embedding the blobstore URL as
an image.

Development process
-------------------

*Consider browsing [the project
commits](https://github.com/philterphactory/Angles-for-Weavrs/commits/master)
at Github for more insight into the development process.*

I started by developing the visualisation as a standalone process,
without considering the integration into Weavrs. I used sample data from
an [existing GEXF export
project](https://github.com/robmyers/Weavrs-API-Access/blob/master/gexf.py)
to bootstrap the process. The [Gephi](http://www.gephi.org)
visualisation tool is available both as a desktop interface and a Java
library. Following the [documentation and
tutorials](http://www.slideshare.net/gephi/gephi-toolkit-tutorialtoolkit)
and given some existing familiarity with Gephi, it's not too hard to
translate an existing visualisation into code. I was provided with
samples in the form of Gephi desktop screenshots by David Bausola and
developed those into a [commandline
equivalent](https://github.com/philterphactory/Angles-for-Weavrs/tree/master/angles-gephi).

Once I had code for a visualisation with a fixed set of parameters, I
worked on parameterising that code so that it could eventually be
customised per Weavr. It made sense to describe the parameters of a
rendering job using a [JSON config
file](https://github.com/philterphactory/Angles-for-Weavrs/blob/master/angles-gephi/sample-render-1.json),
since that would be easy to pass around between components of the
architecture later. I also created a build.xml config for the Ant build
tool so that we could easily build standalone jar files for deployment
later.

After the visualisation was ready, I worked with [Graham
O'Regan](https://github.com/grahamoregan) who created an instance of the
PTK that I could build the prosthetic on. I was able to run this on my
development machine using the Google Appengine toolkit. I experimented
with this to produce a proof-of-concept prosthetic that simply read some
data from the Weavr to which it's attached and output it to the
Appengine log. I also explored publishing blogposts through the same
mechanism. Then I added the Angles-specific code to extract GEXF data
from the Weavr, store it in the persistent state for that Weavr and
create an AnglesRun object for the poller to operate on.

To complete the end-to-end test Graham then added the poller framework
to the project. I was able to run this on my development machine by
pointing its URL settings to my localhost Appengine server. I added basic logging
to show that it was reading AnglesRun data correctly, and we gave it a
test-run. Once that was working, I tested process spawning by adding a
hardcoded run of the renderer to the poller, with a fixed dataset and
parameters, that would run each time. Finally this was replaced with
data taken from the AnglesRun object, and form-multipart posting of the
resulting PNG back to the prosthetic completed the system.

After all this was running correctly, I added an extra web form to the
prosthetic web interface, to be shown to the user after the OAuth
authentication process. This was done using a redirect in the
*post_oauth_callback* method of the prosthetic.

Testing and deployment
----------------------

Deploying the prosthetic web interface was simple - Graham created an
Appengine instance for it and gave me deployment permissions. I was able
to deploy the code directly from the desktop AppEngine Launcher whenever
i liked.

I didn't have access to the server that the poller and renderer would
run on, so I don't have much insight into their deployment. The biggest
delay was caused by Java code that ran fine on my development machine
and on a test VM, but didn't work on the server. This may have been due
to the use of Java 1.6 in devlopment and Java 1.5 on the server. It was
eventually solved by Graham with the addition of some classpath and jar
dependencies. He deployed further updates via a pull from the Github
repository whenever I had pushed a change.

During testing it was beneficial to set the *time_between_runs* in the
prosthetic to a value of 1, meaning that it was possible to run the
cronjob as often as we liked (to generate new AnglesRuns). All prosthetic
crons can be manually run by hitting the path */runner/run_cron* on the
prosthetic's Appengine instance in a web browser. Monitoring its
progress via the application logs in the Appengine control panel was
also essential.

The Django admin pages at the path */admin* were also very useful after
authorising a Weavr with the prosthetic. Using these I was able to check
what OAuth tokens were authorised. I also added a useful diagnostic link to the
AccessToken admin page to [view the Angles
config](https://github.com/philterphactory/Angles-for-Weavrs/commit/b4bec2776db5eb10eb9d436686c6bd71e205445c).
