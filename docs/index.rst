.. Pynac documentation master file, created by
   sphinx-quickstart on Sat Mar 11 13:12:13 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _tested on Python 3.3 to 3.6: https://travis-ci.org/se-esss-litterbox/Pynac
.. _Maybe you should?: http://cyrille.rossant.net/why-you-should-move-to-python-3-now/

Pynac
=====

Pynac is a wrapper around Dynac; an executable used for simulating
the motion of charged particles through accelerator beamlines.  More details can
be found on `the Dynac homepage <https://dynac.web.cern.ch/dynac/dynac.html>`_.

It has been thoroughly `tested on Python 3.3 to 3.6`_, but is known **not** to work
on Python2.  Sorry to those people who haven't yet made the leap to Python3.
(`Maybe you should?`_)

Pynac allows for a very interactive style of use, while also allowing large-scale
simulations to be performed on multi-core, multi-CPU, machines without supervision.
We believe this flexibility is of huge benefit to those designing and modelling
charged-particle beamlines.

Contents
--------
.. toctree::
   :maxdepth: 2

   installation
   modules
   demos
   license
   contact

* :ref:`genindex`
