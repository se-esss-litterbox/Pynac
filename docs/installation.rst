Installation
============

.. _Dynac download page: http://dynac.web.cern.ch/dynac/beta/dynacb.html
.. _the GFortranBinaries page: https://gcc.gnu.org/wiki/GFortranBinaries
.. _inside the Pynac GitHub folder: https://raw.githubusercontent.com/se-esss-litterbox/Pynac/master/Pynac/dynac_unofficial.f

Installation involves two pretty simple steps.  Install Dynac, then install Pynac.

Dynac Installation
------------------
Dynac is distributed as Fortran source.  You'll need Gfortran to compile it, so
start by installing this using your favourite package manager (for example,
``sudo apt-get install gfortran`` should work on Ubuntu/Debian-based systems), or
by downloading the appropriate binary from from `the GFortranBinaries page`_.
Once Gfortran is installed, follow these steps to get Dynac running.

Go to the `Dynac download page`_, and follow the necessary steps to install Dynac on
your system.  Pynac currently assumes that the Dynac executable is called dynacv6_0, so
please make sure to do this.

Pynac Installation
------------------

I recommend working in a virtual environment, but since some people don't like to
do that, I've listed the steps for either case here.

In a virtualenv
+++++++++++++++

To do this you'll need ``virtualenv`` on your system.  ``sudo pip install virtualenv``

1. Make a directory to work in, and move into it -- ``mkdir workingDir && cd workingDir``
2. Create and start a Python3 virtual environment using whatever technique you normally use.  Perhaps as following:

  * ``virtualenv --no-site-packages --python=python3 venv``
  * ``source venv/bin/activate``

3. Install the bokeh plotting library -- ``pip install bokeh``
4. Install Pynac -- ``pip install Pynac``

Not in a virtualenv
+++++++++++++++++++

#. Make a directory to work in, and move into it -- ``mkdir workingDir && cd workingDir``
#. Install the bokeh plotting library -- ``sudo pip install bokeh``
#. Install Pynac -- ``sudo pip install Pynac``
