"""rethink/source_reader.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

This module parses ATS source and creates a python representation of
the input spec in that file.
"""

import os
import rethink.xml.primitives
import rethink.specs

_begin = "/*!"
_end = "*/"

_magic_words = ["OR", "ONE OF", "END", "IF", "THEN", "ELSE", "``[", "EVALUATORS"]

def find_all_comments(stream):
    """Grabs all text contained within _begin, _end pairs."""
    comment_lines = []
    saving = False
    for line in stream:
        if not saving:
            if line.strip().startswith(_begin):
                saving = True
                comment_lines.append(line.strip()[3:])
        elif _end in line:
            # save the partial line
            comment_lines.append(line.split(_end)[0])
            saving = False
        else:
            comment_lines.append(line)
    return comment_lines
                
def to_specname(inname):
    chars = []
    name = inname.replace("_","-")
    
    for i in range(len(name)):
        if name[i].isupper():
            if i is not 0:
                if i+1 < len(name) and name[i+1].islower():
                    chars.append("-")
                elif name[i-1].islower():
                    chars.append("-")
            elif i is not 0 and i+1 == len(name):
                chars.append("-")
                
        chars.append(name[i].lower())
    res =  "".join(chars)+"-spec"
    res = res.replace("--", "-")
    return res

def advance(i,comments):
    """Advances the pointer to the next magic word or parameter"""
    while i < len(comments):
        line = comments[i].strip()
        for mw in _magic_words:
            if line.startswith(mw):
                return i
        if line.startswith("*") and not line.startswith("**"):
            return i
        i += 1
    return i

def parameter_from_lines(lines):
    """Reads a parameter or spec from a set of lines

    Assumes a specification of the form either:

      * `"name`" ``[type]`` **default** documentation

    Where default and documentation are optional.
    """
    fullstring = " ".join([l.strip() for l in lines])
    assert(fullstring.startswith("*") and not fullstring.startswith("**"))
    fullstring = fullstring[1:] # strip the *
    fullstring = fullstring.strip()

    # find the name
    if fullstring.startswith('`"'):
        fullstring = fullstring[2:]

        type_end = fullstring.find('`"')
        if type_end < 0:
            raise RuntimeError('Invalid parameter spec (name) "{0}"'.format(fullstring))
        name = fullstring[0:type_end]
        fullstring = fullstring[type_end+2:].strip()
    else:
        name = "INCLUDE"

    # find the type -- must have one
    if fullstring.startswith('``['):
        fullstring = fullstring[3:]
        type_end = fullstring.find(']``')
        if type_end < 0:
            raise RuntimeError('Invalid parameter spec (type) "{0}"'.format(fullstring))
        ptype = fullstring[0:type_end]
        if name == "INCLUDE":
            name += "-"+ptype
    else:
        raise RuntimeError('Invalid parameter spec (name or type) "{0}"'.format(fullstring))

    # find the remainder and default
    fullstring = fullstring[type_end+3:].strip()
    optional = False
    if fullstring.startswith("**"):
        split_fullstring = fullstring.split("**")
        if len(split_fullstring) < 3:
            raise RuntimeError("Default specification strange, see parameter_from_lines.__doc__")
        default = split_fullstring[1]
        doc = "**".join(split_fullstring[2:]).strip()
        if default == "optional":
            optional = True
            default = None
    else:
        default = None
        doc = fullstring.strip()

    # convert the ptype to primitive
    try:
        ptype = rethink.xml.primitives.xml_to_primitive[ptype]
    except KeyError:
        is_primitive = False
        if default is not None:
            raise RuntimeError('Default issued for non-primitive type "{0}"'.format(ptype))
    else:
        is_primitive = True

    if default is not None:
        default = rethink.xml.primitives.valid_primitive_from_string(ptype, default)

    if is_primitive:
        print("Creating a primitive: %s, %r"%(name, default))
        return rethink.specs.PrimitiveParameter(name, ptype, default, optional)
    else:
        return rethink.specs.DerivedParameter(name, ptype, optional)

def getnext_param(i,comments):
    """Reads a Parameter"""
    assert(comments[i].strip().startswith("*"))

    p = [comments[i],]
    i += 1
    reading = True
    while i < len(comments):
        line = comments[i].strip()
        if len(line) is 0:
            # next line is blank
            return i,parameter_from_lines(p)
        elif line.startswith("*") and not line.startswith("**"):
            # next line is a new parameter
            return i,parameter_from_lines(p)
        else:
            # check if line is a magic work, i.e. OR or other statement
            for magic in _magic_words:
                if line.startswith(magic):
                    return i,parameter_from_lines(p)
            p.append(line)
            i += 1
    return i, parameter_from_lines(p)

def getnext_oneof(i, comments):
    """Reads a ONE OF ... OR ... OR ... block"""
    assert(comments[i].strip().startswith("ONE OF"))
    options = []
    
    while i < len(comments):
        i, junk, objs, junk2 = read_this_scope(i+1, comments)
        assert(junk is None)
        options.append(objs)

        if comments[i].strip().startswith("OR"):
            continue
        elif comments[i].strip().startswith("END"):
            i += 1
            break
        else:
            raise RuntimeError("getnext_oneof broke")

    # quality control
    if len(options) < 2:
        raise RuntimeError("ONE OF: ... OR .. END block not properly formed")
    for opts in options:
        if len(opts) == 0:
            raise RuntimeError("ONE OF: ... OR .. END block not properly formed")
    return i, options

def getnext_evaluators(i, comments):
    """Reads a continuous list of required evaluators."""
    assert(comments[i].strip().startswith("EVALUATORS"))
    reqs = []
    i += 1
    while i < len(comments) and comments[i].strip().startswith("-"):
        reqs.append(comments[i].strip().split('`"')[1])
        i += 1
    return i, reqs

def getnext_or(i, comments):
    """Throws on naked OR"""
    assert(comments[i].strip().startswith("OR"))
    # a naked or is an error
    raise RuntimeError("naked or")

def getnext_if(i, comments):
    """Reads an IF ... THEN ... ELSE ... ENDIF block"""
    assert(comments[i].strip().startswith("IF"))
    # not yet implemented
    raise NotImplementedError("not yet implemented")

def getnext_then(i,comments):
    """Reads an IF ... THEN ... ELSE ... ENDIF block"""
    assert(comments[i].strip().startswith("THEN"))
    # not yet implemented
    raise NotImplementedError("not yet implemented")

def getnext_else(i,comments):
    """Reads an IF ... THEN ... ELSE ... ENDIF block"""
    assert(comments[i].strip().startswith("ELSE"))
    # not yet implemented
    raise NotImplementedError("not yet implemented")

def read_this_scope(i, comments):
    required_evaluators = []
    objects = []
    specname = None
    i = advance(i, comments)

    if i < len(comments):
        line = comments[i].strip()
        if line.startswith("``["):
            specname = line[3:].split("]``")[0]
            i = advance(i+1,comments)

    while i < len(comments):
        line = comments[i]
        if line.startswith("*") and not line.startswith("**"):
            i, obj = getnext_param(i, comments)
            if type(obj) is str or not obj.name.startswith("_"):
                # note in real code obj is a type, but in test code
                # it can be a string.  So rather than do more mocking work,
                # we'll just test it here.
                objects.append(obj)
        elif line.startswith("ONE OF"):
            i, obj = getnext_oneof(i, comments)
            objects.append(obj)
        elif line.startswith("IF"):
            i, obj = getnext_if(i, comments)
            objects.append(obj)
        elif line.startswith("EVALUATOR"):
            i, reqs = getnext_evaluators(i, comments)
            required_evaluators.extend(reqs)
        else:
            # exit the scope
            break
        i = advance(i, comments)
        
    return i, specname, objects, required_evaluators

def read(filename):
    with open(filename, 'r') as fid:
        comments = find_all_comments(fid)
    return read_lines(os.path.split(filename)[-1][:-3], comments)

def read_lines(name, comments):
    specs = []
    i = 0
    while i < len(comments):
        i, specname, objects, reqs = read_this_scope(i,comments)
        if specname is None:
            specname = to_specname(name)
        if len(objects) > 0:
            specs.append((specname, objects, reqs))
    return specs
