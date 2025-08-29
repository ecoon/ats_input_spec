"""ats_input_spec/primitives.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Module for working with primitive parameter types.
"""


class ListBool(object):
    ptype = bool

class ListFloat(object):
    ptype = float

class ListInt(object):
    ptype = int

class ListStr(object):
    ptype = str

valid_primitives = [float, int, str, bool]
valid_list_primitives = [ListBool,ListFloat,ListInt,ListStr]
valid_types = valid_primitives + valid_list_primitives

text_to_primitive = {'double':float,
                    'int':int,
                    'string':str,
                    'bool':bool,
                    'Array(double)':ListFloat,
                    'Array(int)':ListInt,
                    'Array(string)':ListStr,
                    'Array(bool)':ListBool
                    }

primitives_to_text = {float:"double",
                      int:"int",
                      str:"string",
                      bool:"bool",
                      ListFloat:"Array(double)",
                      ListInt:"Array(int)",
                      ListStr:"Array(string)",
                      ListBool:"Array(bool)",
                      }

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



# def print_primitive_type(ptype):
#     """Pretty-printing of types"""
#     try:
#         return text_primitives[ptype]
#     except KeyError:
#         return ptype.specname

def valid_float_from_string(value):
    try:
        retval = float(value)
    except ValueError:
        raise RuntimeError("Parameter of type double with invalid value \"%s\""%str(value))
    return retval

def valid_int_from_string(value):
    if 'e' in value:
        left_right = value.split('e')
        if (len(left_right) != 2):
            raise ValueError("Parameter of type int with invalid value \"%s\""%str(value))
        try:
            left = valid_int_from_string(left_right[0])
            right = valid_int_from_string(left_right[1])
        except ValueError:
            raise ValueError("Parameter of type int with invalid value \"%s\""%str(value))
        return left * 10**right
        
    try:
        retval = int(value)
    except ValueError:
        try:
            return int(float(value))
        except ValueError:
            raise RuntimeError("Parameter of type int with invalid value \"%s\""%str(value))
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
    elif ptype is ListFloat:
        return [valid_float_from_string(p) for p in list_from_string(value)]
    elif ptype is ListInt:
        return [valid_int_from_string(p) for p in list_from_string(value)]
    elif ptype is ListBool:
        return [valid_bool_from_string(p) for p in list_from_string(value)]
    elif ptype is ListStr:
        return list_from_string(value)

def string_from_primitive(value):
    if type(value) is str:
        return value
    elif type(value) is int:
        return str(value)
    elif type(value) is bool:
        if value:
            return "true"
        else:
            return "false"
    elif type(value) is float:
        return '%2.8f'%value
    elif type(value) is list:
        assert(len(value) > 0)
        t0 = type(value[0])
        value = [valid_from_type(t0, v) for v in value]
        return '{'+','.join([string_from_primitive(v) for v in value])+'}'

