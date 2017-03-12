Installation
============

.. _Dynac download page: http://dynac.web.cern.ch/dynac/beta/dynacb.html
.. _the GFortranBinaries page: https://gcc.gnu.org/wiki/GFortranBinaries

Installation involves two pretty simple steps.  First install Dynac, then Pynac.

Dynac Installation
------------------
Dynac is an executable that is distributed as Fortran source.  You will need Gfortran
to compile this, so start by downloading the appropriate binary from from
`the GFortranBinaries page`_.

#. Download the Dynac source file (Fortran) from the `Dynac download page`_.
#. Compile with ``gfortran``.  Pynac currently assumes that the executable is called ``dynacv6_0``, but this will be configurable in future releases.
#. Put the executable into the system path

Pynac Installation
------------------

As is usual with Python code, I recommend installing this in a virtual environment,
however you may not want to do that.  I've listed the steps for both cases here.

In a virtualenv
+++++++++++++++

To do this you'll need ``virtualenv`` on your system.  ``sudo pip install virtualenv``

#. Grab the code from Github -- ``git clone https://github.com/se-esss-litterbox/Pynac.git``
#. Move into the newly downloaded directory -- ``cd Pynac``
#. Create a Python3 virtual environment -- ``virtualenv --no-site-packages --python=python3 venv``
#. Start the virtual environment -- ``source venv/bin/activate``
#. Install the required packages -- ``pip install -r requirements.txt``

Not in a virtualenv
+++++++++++++++++++

#. Grab the code from Github -- ``git clone https://github.com/se-esss-litterbox/Pynac.git``
#. Move into the newly downloaded directory -- ``cd Pynac``
#. Install the required packages -- ``sudo pip install -r requirements.txt``
