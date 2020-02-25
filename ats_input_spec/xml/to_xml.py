"""rethink/xml/to_xml.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Takes a rethink parameter instance and generates the corresponding xml.
"""

from rethink.xml import etree
import rethink.primitives

def primitive_to_xml(name, obj):
    """Returns xml for a Parameter"""
    xml = etree.Element("Parameter")
    xml.set("name", name)
    if type(obj) in rethink.primitives.valid_primitives:
        xml.set("type", rethink.primitives.text_primitives[type(obj)])
        xml.set("value", "%r"%obj)
    elif type(obj) is list:
        type0 = type(obj[0])
        assert(type0 in rethink.primitives.valid_primitives)
        xml.set("type", "Array(%s)"%rethink.primitives.text_primitives[type0])
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
    if rethink.primitives.is_primitive(type(obj)):
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
    
    
