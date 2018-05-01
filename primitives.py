"""rethink/primitives.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Module for working with primitive parameter types.
"""

valid_primitives = [float, int, str, bool]

class ListBool(object):
    ptype = bool

class ListFloat(object):
    ptype = float

class ListInt(object):
    ptype = int

class ListStr(object):
    ptype = str

valid_list_primitives = [ListBool,ListFloat,ListInt,ListStr]

valid_types = valid_primitives + valid_list_primitives


def valid_from_type(ptype, value):
    """Returns value interpreted as a ptype."""
    if ptype not in valid_types:
        raise TypeError('Parameter Validation: Type "{0}" not in valid types.'.format(ptype))

    if value is None:
        return value

    if type(value) is ptype:
        return value

    if ptype is bool:
        if type(value) is int and (value == 0 or value == 1):
            return bool(value)
        elif type(value) is str:
            if value == "True" or value == "TRUE" or value == "true":
                return True
            elif value == "False" or value == "FALSE" or value == "false":
                return False

    elif ptype is int:
        if type(value) is str:
            try:
                return int(value)
            except ValueError:
                pass

    elif ptype is float:
        if type(value) is int:
            return float(value)
        elif type(value) is str:
            try:
                return float(value)
            except ValueError:
                pass

    elif ptype in valid_list_primitives:
        if type(value) is list:
            return [valid_from_type(ptype.ptype, v) for v in value]

    raise TypeError('Parameter Validation: Value "{0}" cannot be interpreted as "{1}"'.format(value,ptype))



text_primitives = {float:"double",
                   int:"int",
                   str:"string",
                   bool:"bool",
                   ListFloat:"Array(double)",
                   ListInt:"Array(int)",
                   ListStr:"Array(string)",
                   ListBool:"Array(bool)",
                   }

def print_primitive_type(ptype):
    """Pretty-printing of types"""
    try:
        return text_primitives[ptype]
    except KeyError:
        return ptype.specname

def is_primitive(ptype):
    """Is this type a primitive?"""
    return ptype in text_primitives.keys()

            
            
