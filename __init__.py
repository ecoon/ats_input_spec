"""rethink/__init__.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Rethink is a library for creating ATS input files.  Input files are
governed by a series of specs, which are defined in the code.  Specs
are maintained only in the Amanzi/ATS source code comments, and
slurped in here.

This init simply controls paths to Amanzi and ATS source code.
"""

import os

AMANZI_SRC_DIR = None
ATS_SRC_DIR = None

def set_amanzi_source(path):
    """Sets the path to search for Amanzi specs"""
    global AMANZI_SRC_DIR
    AMANZI_SRC_DIR = path

def set_ats_source(path):
    """Sets the path to search for ATS specs"""
    global ATS_SRC_DIR
    ATS_SRC_DIR = path

try:
    set_amanzi_source(os.environ['AMANZI_SRC_DIR'])
except KeyError:
    print("AMANZI_SRC_DIR not found in env: be sure to call rethink.set_amanzi_source()")

try:
    set_ats_source(os.environ['ATS_SRC_DIR'])
except KeyError:
    print("ATS_SRC_DIR not found in env: be sure to call rethink.set_ats_source()")
    
    
    
