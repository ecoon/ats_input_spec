"""ats_input_spec/xml/primitives.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Module for mapping from XML strings to python types.
"""

import ats_input_spec.primitives as rp

xml_to_primitive = {'double':float,
                    'int':int,
                    'string':str,
                    'bool':bool,
                    'Array(double)':rp.ListFloat,
                    'Array(int)':rp.ListInt,
                    'Array(string)':rp.ListStr,
                    'Array(bool)':rp.ListBool
                    }


def valid_float_from_string(value):
    try:
        retval = float(value)
    except ValueError:
        raise RuntimeError("Parameter of type double with invalid value \"%s\""%str(value))
    return retval


def valid_int_from_string(value):
    try:
        retval = int(value)
    except ValueError:
        raise RuntimeError("Parameter of type double with invalid value \"%s\""%str(value))
    return retval


def valid_bool_from_string(value):
    if value == "true":
        retval = True
    elif value == "True":
        retval = True
    elif value == "TRUE":
        retval = True
    elif value == "false":
        retval = False
    elif value == "False":
        retval = False
    elif value == "FALSE":
        retval = False
    else:
        raise RuntimeError('Parameter of type bool with invalid value "{0}"'.format(value))
    return retval


def list_from_string(value):
    assert(type(value) is str)
    inner = value.strip()
    assert(inner[0] == "{")
    assert(inner[-1] == "}")
    return inner[1:-1].split(",")
    

def valid_primitive_from_string(ptype, value):
    assert(type(value) is str)
    if type(ptype) is str:
        ptype = xml_to_primitive[ptype]

    if ptype is int:
        return valid_int_from_string(value)
    elif ptype is float:
        return valid_float_from_string(value)
    elif ptype is bool:
        return valid_bool_from_string(value)
    elif ptype is str:
        return value
    elif ptype is rp.ListFloat:
        return [valid_float_from_string(p) for p in list_from_string(value)]
    elif ptype is rp.ListInt:
        return [valid_int_from_string(p) for p in list_from_string(value)]
    elif ptype is rp.ListBool:
        return [valid_bool_from_string(p) for p in list_from_string(value)]
    elif ptype is rp.ListStr:
        return list_from_string(value)


                    
                        
                        

