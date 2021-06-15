"""ats_input_spec/printing.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Pretty printing.
"""

import ats_input_spec.colors
import ats_input_spec.primitives
import ats_input_spec.specs


def help(name, obj, optional=True):
    lines = _help(name, obj, optional)
    print('\n'.join(lines))

        
    

