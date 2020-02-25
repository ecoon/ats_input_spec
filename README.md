ATS Input Spec
---------------

Author: Ethan Coon (coonet@ornl.gov)

This is progress toward a capability for parsing/reading ATS and
Amanzi source code to generate docstrings, which in turn are used to
generate self-filling dictionaries, which can then be used from python
code and scripts to generate ATS input files.

The capability is fairly general and the framework is fairly set.
Remaining holes in generating full input files are largely due to a
need for:

1. More complete coverage of docstrings in ATS and Amanzi source code.

2. Special helper functions in python for making some of the specs
   easier to use.

WORK IN PROGRESS!  BUYER BEWARE!

