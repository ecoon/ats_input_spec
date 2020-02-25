"""ats_input_spec/xml/to_xml.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Takes a ats_input_spec parameter instance and generates the corresponding xml.
"""

from ats_input_spec.xml import etree
import ats_input_spec.primitives

def primitive_to_xml(name, obj):
    """Returns xml for a Parameter"""
    xml = etree.Element("Parameter")
    xml.set("name", name)
    if type(obj) in ats_input_spec.primitives.valid_primitives:
        xml.set("type", ats_input_spec.primitives.text_primitives[type(obj)])
        xml.set("value", "%r"%obj)
    elif type(obj) is list:
        type0 = type(obj[0])
        assert(type0 in ats_input_spec.primitives.valid_primitives)
        xml.set("type", "Array(%s)"%ats_input_spec.primitives.text_primitives[type0])
        xml.set("value", "{"+",".join(["%r"%ob for ob in obj])+"}")
    return xml
    
def derived_to_xml(name, obj):
    """Returns xml for a ParameterList"""
    xml = etree.Element("ParameterList")
    xml.set("name", name)
    xml.set("type", type(obj).__name__)
    for k,v in obj.items():
        xml.append(obj_to_xml(k,v))
    return xml


def obj_to_xml(name, obj):
    """Returns xml for a Parameter or ParameterList"""
    if ats_input_spec.primitives.is_primitive(type(obj)):
        return primitive_to_xml(name, obj)
    else:
        return derived_to_xml(name, obj)

def to_xml(main):
    """Returns xml for a full ATS spec."""
    return obj_to_xml("Main", main)

def write(main, filename):
    """Write xml file for a full ATS spec."""
    xml = to_xml(main)
    xml.write(filename, pretty_print=True)
    
    
