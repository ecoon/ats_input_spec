"""ats_input_spec/source_reader.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

This module parses ATS source and creates a python representation of
the input spec in that file.
"""

import os
import ats_input_spec.xml.primitives
import ats_input_spec.specs
import logging

_begin = "/*!"
_end = "*/"

_magic_words = ["OR",
                "ONE OF",
                "END",
                "IF",
                "THEN",
                "ELSE",
                "``[",
                ".. admonition:",
                "EVALUATORS"]

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
            if i != 0:
                if i+1 < len(name) and name[i+1].islower():
                    chars.append("-")
                elif name[i-1].islower():
                    chars.append("-")
            elif i != 0 and i+1 == len(name):
                chars.append("-")
                
        chars.append(name[i].lower())
    res =  "".join(chars)+"-spec"
    res = res.replace("--", "-")
    return res

def advance(i,comments):
    """Advances the pointer to the next magic word or parameter"""
    logging.info(f"advancing!")
    while i < len(comments):
        line = comments[i].strip()
        logging.debug(f"advancing line: {line}")
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
        ptype = ats_input_spec.xml.primitives.xml_to_primitive[ptype]
    except KeyError:
        is_primitive = False
        if default is not None:
            raise RuntimeError('Default issued for non-primitive type "{0}"'.format(ptype))
    else:
        is_primitive = True

    if default is not None:
        default = ats_input_spec.xml.primitives.valid_primitive_from_string(ptype, default)

    if is_primitive:
        print("Creating a primitive: %s, %r"%(name, default))
        return ats_input_spec.specs.PrimitiveParameter(name, ptype, default, optional)
    else:
        return ats_input_spec.specs.DerivedParameter(name, ptype, optional)

def getnext_param(i,comments):
    """Reads a Parameter"""
    logging.debug(f"  reading parameter")
    assert(comments[i].strip().startswith("*"))

    p = [comments[i],]
    i += 1
    reading = True
    while i < len(comments):
        line = comments[i].strip()
        if len(line) == 0:
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
    logging.debug(f"  reading ONE OF")
    assert(comments[i].strip().startswith("ONE OF"))
    options = ats_input_spec.specs.OneOfList()
    
    while i < len(comments):
        i, junk, objs, junk2 = read_this_scope(i+1, comments)
        assert(junk is None)
        options.append(objs)

        line = comments[i].strip()
        logging.debug(f'in ONE OF, delimiter line = {line}')
        if line.startswith("OR"):
            continue
        elif line.startswith("END"):
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
    logging.debug(f"  reading EVALUATORS")
    assert(comments[i].strip().startswith("EVALUATORS"))
    reqs = []
    i += 1
    while i < len(comments) and comments[i].strip().startswith("-"):
        reqs.append(comments[i].strip().split('`"')[1])
        i += 1
    return i, reqs

def getnext_keys(i, comments):
    """Reads a continuous list of optional key names."""
    logging.debug(f"  reading KEYS")
    assert(comments[i].strip().startswith("KEYS"))
    reqs = []
    i += 1
    while i < len(comments) and \
          comments[i].strip().startswith("-"):
        reqs.append(comments[i].strip().split('`"')[1])
        i += 1
    return i, reqs



def getnext_if(i, comments):
    """Reads an IF ... THEN ... ELSE ... ENDIF block"""
    logging.debug(f"  reading IF")
    assert(comments[i].strip().startswith("IF"))
    cond_true_false = ats_input_spec.specs.Conditional()

    # read the conditional, always present
    i, junk, objs, junk2 = read_this_scope(i+1, comments)
    assert(junk is None)
    if len(objs) != 1:
        raise RuntimeError('Conditional IF may only have one boolean parameter.')
    cond_true_false.append(objs)

    line = comments[i].strip()
    logging.debug(f'in IF, delimiter line = {line}')

    # check for then block
    if line.startswith("THEN"):
        i, junk, objs, junk2 = read_this_scope(i+1, comments)
        assert(junk is None)
        cond_true_false.append(objs)

        line = comments[i].strip()
        logging.debug(f'after THEN, delimiter line = {line}')
    else:
        # no THEN block
        cond_true_false.append(list())

    # check for ELSE block
    if line.startswith("ELSE"):
        i, junk, objs, junk2 = read_this_scope(i+1, comments)
        assert(junk is None)
        cond_true_false.append(objs)

        line = comments[i].strip()
        logging.debug(f'after ELSE, delimiter line = {line}')
    else:
        # no ELSE block
        cond_true_false.append(list())

    if not line.startswith("END"):
        raise RuntimeError("Unclosed IF..THEN...ELSE...END block")
    return i+1, cond_true_false


def read_this_scope(i, comments):
    """Read a single scope starting at line i and ending at either an END
    or other marker ending the scope (e.g. a line of text that is not
    indented, isn't a parameter, and doesn't start with a magic word).
    """
    scope_begin_i = i
    logging.debug(f"reading scope starting at line: {i} = {comments[i]}")
    required_evaluators = []
    optional_keys = []
    objects = []
    specname = None
    i = advance(i, comments)

    if i < len(comments):
        line = comments[i].strip()
        if line.startswith("``["):
            specname = line[3:].split("]``")[0]
            logging.debug(f"found specname: {specname}")
            i = advance(i+1,comments)
        elif line.startswith(".. admonition::"):
            specname = line[len(".. admonition:: "):].strip().strip(':')
            logging.debug(f"found specname: {specname}")
            i = advance(i+1,comments)

    while i < len(comments):
        line = comments[i].strip()
        logging.debug(f"reading line: {line}")

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
        elif line.startswith("KEYS"):
            i, reqs = getnext_keys(i, comments)
            optional_keys.extend(reqs)
        else:
            # exit the scope
            break
        i = advance(i, comments)
        
    logging.debug(f"done reading scope ranging from {scope_begin_i} to {i}")
    return i, specname, objects, (required_evaluators, optional_keys)

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
