Installation
============

.. _Dynac download page: http://dynac.web.cern.ch/dynac/beta/dynacb.html
.. _the GFortranBinaries page: https://gcc.gnu.org/wiki/GFortranBinaries

Proper installation instructions will come soon, but for the moment it follows
the standard Python style.  If you don't understand the following, you're probably
not a Python dev., and so should wait for the proper instructions to be written
(super soon -- I promise).

#. Grab the code from Github -- ``git clone https://github.com/se-esss-litterbox/Pynac.git``
#. Move into the newly downloaded directory -- ``cd Pynac``
#. Create a Python3 virtual environment -- ``virtualenv --no-site-packages --python=python3 venv``
#. Start the virtual environment -- ``source venv/bin/activate``
#. Install the required packages -- ``pip install -r requirements.txt``
#. Download the Dynac source file (Fortran) from the `Dynac download page`_.
#. Compile with ``gfortran`` and make sure the executable is in your path.  Gfortran binaries can be downloaded from `the GFortranBinaries page`_.
