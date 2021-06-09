"""ats_input_spec/__init__.py

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
import logging

#
# Set source directories
#
AMANZI_SRC_DIR = None
def set_amanzi_source(path):
    """Sets the path to search for Amanzi specs"""
    global AMANZI_SRC_DIR
    AMANZI_SRC_DIR = path

try:
    set_amanzi_source(os.environ['AMANZI_SRC_DIR'])
except KeyError:
    print("AMANZI_SRC_DIR not found in env: be sure to call ats_input_spec.set_amanzi_source()")

#
# Set log verbosity level
#
verb_to_level = {0:logging.WARNING,
                 1:logging.INFO,
                 2:logging.DEBUG,
                 3:logging.DEBUG}
def setup_logging(verbosity, logfile=None):
    """Sets the log level and log file."""
    level = verb_to_level[verbosity]
    
    if type(logfile) is str:
        raise RuntimeError("Developer error: use 'with open() as fid' construct instead.")

    if logfile is not None:
        logging.basicConfig(filename=logfile, level=level,
                            format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=level,
                            format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')


#
# load known specs from source
#
def load_known_specs():
    import ats_input_spec.known_specs
    ats_input_spec.known_specs.load()
        
    
    
    
