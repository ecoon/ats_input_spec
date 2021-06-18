"""ats_input_spec/xml/to_xml.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Takes a ats_input_spec parameter instance and generates the corresponding xml.
"""

import warnings
import ats_input_spec.primitives
import amanzi_xml.common.parameter
import amanzi_xml.common.parameter_list
import amanzi_xml.utils.parser
import amanzi_xml.utils.io

def primitive_to_xml(par):
    """Returns xml for a Parameter"""
    return amanzi_xml.utils.parser.objects[par.ptype_string](par.name, par.get())
    
def derived_to_xml(par):
    """Returns xml for a ParameterList"""
    plist = amanzi_xml.common.parameter_list.ParameterList(par.name)

    for p in par.get().parameters():
        if p.has_value():
            plist.append(obj_to_xml(p))
    return plist

def obj_to_xml(par):
    """Returns xml for a Parameter or ParameterList"""
    if par.is_primitive():
        return primitive_to_xml(par)
    else:
        return derived_to_xml(par)

def to_xml(main):
    """Returns xml for a full ATS spec."""
    main_par = ats_input_spec.specs.Parameter('Main', value=main)
    if not main_par.is_complete():
        warnings.warn('Creating an incomplete XML object, missing entries!')
    return obj_to_xml(main_par)

def write(main, filename):
    """Write xml file for a full ATS spec."""
    xml = to_xml(main)
    amanzi_xml.utils.io.toFile(xml, filename)
    
    
