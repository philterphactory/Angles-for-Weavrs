Development experience creating a media-producing prosthetic for Weavrs
=======================================================================

*Author: Matt Biddulph*

*June 2012*

In two weeks in May 2012 I created the code in [Angles For
Weavrs](https://github.com/philterphactory/Angles-for-Weavrs). It's a
mixture of Python/Django and Java code that creates a graph
visualisation of a Weavr's keyword usage over the preceding week. This
document records the process of creating the code.

[diagram]

Architecture and software components
------------------------------------

The components of the system are:

1. Prosthetic web interface (Python using Django on Google appengine)
2. Prosthetic job poller (Python)
3. Commandline graph-visualisation renderer (Java using Gephi)

The web interface is used to add the prosthetic to an individual Weavr
via the usual OAuth flow. After a Weavr has been authenticated and the
tokens added to the prosthetic's appengine database, a configuration
screen is shown where the user can customise some parameters of the
visualisation. The PTK uses appengine's cron mechanism to call the *act*
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
on appengine (e.g. java AWT graphics toolkit), it's necessary to run it
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
appengine *blobstore* mechanism for serving large files, and notes the
generated URL. Then it calls the */1/weavr/post* API to create a
blogpost for the intended Weavr, directly embedding the blobstore URL as
an image.

Development process
-------------------



Testing
-------
