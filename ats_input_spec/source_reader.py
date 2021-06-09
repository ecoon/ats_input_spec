"""ats_input_spec/source_reader.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

This module parses ATS source and creates a python representation of
the input spec in that file.
"""

import os
import logging
import ats_input_spec.xml.primitives
import ats_input_spec.specs
import logging

_begin = "/*!"
_end = "*/"


_spec_starters = ["``[", ".. admonition::"]
_magic_words = ["OR",
                "ONE OF",
                "END",
                "IF",
                "THEN",
                "ELSE",
                "EVALUATORS",
                "INCLUDES"
                ] + _spec_starters

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
        elif line.startswith("-"):
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
    fullstring = fullstring.strip() # strip remaining whitespace

    # find the name
    if fullstring.startswith('`"'):
        fullstring = fullstring[2:]
        type_end = fullstring.find('`"')
        if type_end < 0:
            raise RuntimeError('Invalid parameter spec (name) "{0}"'.format(fullstring))
        name = fullstring[0:type_end]
        fullstring = fullstring[type_end+2:].strip()
    elif fullstring.startswith('"'):
        fullstring = fullstring[1:]
        type_end = fullstring.find('"')
        if type_end < 0:
            raise RuntimeError('Invalid parameter spec (name) "{0}"'.format(fullstring))
        name = fullstring[0:type_end]
        fullstring = fullstring[type_end+1:].strip()
    else:
        raise RuntimeError('Invalid parameter spec (name) "{0}"'.format(fullstring))

    # find the type -- must have one
    if fullstring.startswith('``['):
        fullstring = fullstring[3:]
        type_end = fullstring.find(']``')
        if type_end < 0:
            raise RuntimeError(f'Invalid parameter spec (type) for {name} on line "{fullstring}"')
        ptype = fullstring[0:type_end]
        fullstring = fullstring[type_end+3:].strip()
    elif fullstring.startswith('['):
        fullstring = fullstring[1:]
        type_end = fullstring.find(']')
        if type_end < 0:
            raise RuntimeError(f'Invalid parameter spec (type) for {name} on line "{fullstring}"')
        ptype = fullstring[0:type_end]
        fullstring = fullstring[type_end+1:].strip()
    else:
        raise RuntimeError(f'Invalid parameter spec (type) for {name} on line "{fullstring}"')

    # find the default, set the optional flag, and the rest is the docstring
    optional = False
    split_fullstring = fullstring.split("**")
    if fullstring.startswith("**") and len(split_fullstring) >= 3:
        default = split_fullstring[1]
        optional = True
        docstring = "**".join(split_fullstring[2:]).strip()
        if default == "optional":
            optional = True
            default = None
    else:
        default = None
        docstring = fullstring.strip()

    # convert the ptype to primitive
    try:
        ptype = ats_input_spec.xml.primitives.xml_to_primitive[ptype]
    except KeyError:
        is_primitive = False
        if default is not None:
            raise RuntimeError('Default issued for non-primitive type "{0}"'.format(ptype))
    else:
        is_primitive = True

    # convert the default to a primitive
    if default is not None:
        default = ats_input_spec.xml.primitives.valid_primitive_from_string(ptype, default)

    # return the spec object
    if is_primitive:
        logging.debug("Creating a primitive: %s, %r"%(name, default))
        return ats_input_spec.specs.PrimitiveParameter(name, ptype, default, optional)
    else:
        return ats_input_spec.specs.DerivedParameter(name, ptype, optional)

def getnext_param(i_in, comments):
    """Reads a Parameter"""
    logging.debug(f"  reading parameter")
    assert(comments[i_in].strip().startswith("*"))

    # we have to detect when to stop reading this parameter's lines.
    # This is set by a blank line, another parameter, or a magic word,
    # but not an item.
    p = [comments[i_in],]
    i = i_in + 1
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


def item_from_lines(lines):
    """Reads an item from a set of lines.

    Items are of the form

      - `"name`" **default** documentation

    Where default and documentation are optional.  Typically these are
    used for KEYS, INCLUDES, and eventually VALID sections.

    """
    fullstring = " ".join([l.strip() for l in lines])
    assert(fullstring.startswith("-"))
    fullstring = fullstring[1:] # strip the -
    fullstring = fullstring.strip() # strip remaining whitespace

    # find the name
    if fullstring.startswith('`"'):
        fullstring = fullstring[2:]
        type_end = fullstring.find('`"')
        if type_end < 0:
            raise RuntimeError('Invalid item spec (name) "{0}"'.format(fullstring))
        name = fullstring[0:type_end]
        fullstring = fullstring[type_end+2:].strip()
    elif fullstring.startswith('"'):
        fullstring = fullstring[1:]
        type_end = fullstring.find('"')
        if type_end < 0:
            raise RuntimeError('Invalid item spec (name) "{0}"'.format(fullstring))
        name = fullstring[0:type_end]
        fullstring = fullstring[type_end+1:].strip()
    elif fullstring.startswith('``['):
        fullstring = fullstring[3:]
        type_end = fullstring.find(']``')
        if type_end < 0:
            raise RuntimeError('Invalid item spec (name) "{0}"'.format(fullstring))
        name = fullstring[0:type_end]
        fullstring = fullstring[type_end+3:].strip()
    else:
        raise RuntimeError('Invalid item spec (name) "{0}"'.format(fullstring))

    # find the default, set the optional flag, and the rest is the docstring
    optional = False
    split_fullstring = fullstring.split("**")
    if fullstring.startswith("**") and len(split_fullstring) >= 3:
        default = split_fullstring[1]
        optional = True
        docstring = "**".join(split_fullstring[2:]).strip()
        if default == "optional":
            optional = True
            default = None
    else:
        default = None
        docstring = fullstring.strip()

    return name, default, optional, docstring


def getnext_item(i_in, comments):
    """Reads an item, which is a simple string, potentially plus a
    default, plus a docstring (e.g. an untyped parameter)
    """
    logging.debug(f"  reading item")
    assert(comments[i_in].strip().startswith('-'))

    # we have to detect when to stop reading this item's lines.  This
    # is set by a blank line, another item, a parameter, or a magic
    # word.
    p = [comments[i_in],]
    i = i_in + 1
    reading = True
    while i < len(comments):
        line = comments[i].strip()
        if len(line) == 0:
            # next line is blank
            return i,item_from_lines(p)
        elif line.startswith("*") and not line.startswith("**"):
            # next line is a new parameter
            return i,item_from_lines(p)
        elif line.startswith("-"):
            # next line is a new item
            return i,item_from_lines(p)
        else:
            # check if line is a magic work, i.e. OR or other statement
            for magic in _magic_words:
                if line.startswith(magic):
                    return i,item_from_lines(p)
        p.append(line)
        i += 1
    return i, item_from_lines(p)
                       

def getnext_oneof(i_in, comments):
    """Reads a ONE OF ... OR ... OR ... block"""
    logging.debug(f"  reading ONE OF")
    assert(comments[i_in].strip().startswith("ONE OF"))
    options = ats_input_spec.specs.OneOfList()

    i = i_in + 1
    while i < len(comments):
        i_new, junk, objs, junk2 = read_this_scope(i, comments)
        assert(i_new >= i)
        i = i_new
        assert(junk is None)
        options.append(objs)

        line = comments[i].strip()
        logging.debug(f'in ONE OF, delimiter line = {line}')
        if line.startswith("OR"):
            i += 1
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


def getnext_evaluators(i_in, comments):
    """Reads a continuous list of required evaluators."""
    logging.debug(f"  reading EVALUATORS")
    assert(comments[i_in].strip().startswith("EVALUATORS"))
    reqs = []
    i = advance(i_in+1, comments)
    while i < len(comments):
        line = comments[i].strip()
        if line.startswith('-'):
            i, item = getnext_item(i, comments)
            reqs.append(item)
        i += 1
    return i, reqs

def getnext_keys(i_in, comments):
    """Reads a list of key names."""
    logging.debug(f"  reading KEYS")
    assert(comments[i_in].strip().startswith("KEYS"))
    keys = []
    i = advance(i_in+1, comments)
    while i < len(comments):
        line = comments[i].strip()
        if line.startswith('-'):
            i, item = getnext_item(i, comments)
            keys.append(item)
        else:
            break
    return i, keys

def getnext_includes(i_in, comments):
    """Reads a list of included names."""
    logging.debug(f"  reading INCLUDES")
    assert(comments[i_in].strip().startswith("INCLUDES"))
    includes = []
    i = advance(i_in+1, comments)
    while i < len(comments):
        line = comments[i].strip()
        if line.startswith('-'):
            i, item = getnext_item(i, comments)
            includes.append(item)
        else:
            break
    return i, includes

def getnext_if(i_in, comments):
    """Reads an IF ... THEN ... ELSE ... ENDIF block"""
    logging.debug(f"  reading IF")
    assert(comments[i_in].strip().startswith("IF"))
    cond_true_false = ats_input_spec.specs.Conditional()

    # read the conditional, always present
    i, junk, objs, junk2 = read_this_scope(i_in+1, comments)
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


def read_this_scope(i_in, comments):
    """Read a single scope starting at line i and ending at either an END
    or other marker ending the scope.
    """
    logging.debug(f"reading scope starting at line: {i_in} = {comments[i_in]}")
    required_evaluators = []
    keys = []
    includes = []
    objects = []
    specname = None

    i = advance(i_in, comments)
    if i < len(comments):
        line = comments[i].strip()
        # a new spec begins
        if line.startswith("``["):
            specname = line[3:].split("]``")[0]
            logging.debug(f"found specname: {specname}")
            i = advance(i+1,comments)
        elif line.startswith(".. admonition::"):
            specname = line[len(".. admonition::"):].strip().strip(':')
            logging.debug(f"found specname: {specname}")
            i = advance(i+1,comments)

    while i < len(comments):
        line = comments[i].strip()
        logging.debug(f"reading line: {line}")

        if line.startswith("*") and not line.startswith("**"):
            i_new, obj = getnext_param(i, comments)
            assert(i_new > i)
            i = i_new
            if type(obj) is str or not obj.name.startswith("_"):
                # note in real code obj is a type, but in test code
                # it can be a string.  So rather than do more mocking work,
                # we'll just test it here.
                objects.append(obj)
        elif line.startswith("ONE OF"):
            i_new, obj = getnext_oneof(i, comments)
            assert(i_new > i)
            i = i_new
            objects.append(obj)
        elif line.startswith("IF"):
            i_new, obj = getnext_if(i, comments)
            assert(i_new > i)
            i = i_new
            objects.append(obj)

        elif line.startswith("EVALUATOR"):
            i_new, reqs = getnext_evaluators(i, comments)
            assert(i_new > i)
            i = i_new
            required_evaluators.extend(reqs)
        elif line.startswith("KEYS"):
            i_new, keys = getnext_keys(i, comments)
            assert(i_new > i)
            i = i_new
            keys.extend(keys)
        elif line.startswith("INCLUDES"):
            i_new, incs = getnext_includes(i, comments)
            assert(i_new > i)
            i = i_new
            includes.extend(incs)
        elif line.startswith("-"):
            # items are not processed in a scope, likely this is a RST
            # list in the documentation, not a true item.  Continue.
            i += 1
        else:
            # exit the scope
            break
        i = advance(i, comments)
        
    logging.debug(f"done reading scope ranging from {i_in} to {i}")
    return i, specname, objects, (required_evaluators, keys, includes)

def read(filename):
    with open(filename, 'r') as fid:
        comments = find_all_comments(fid)
    return read_lines(os.path.split(filename)[-1][:-3], comments)

def read_lines(name, comments):
    specs = []
    i = 0
    while i < len(comments):
        i_new, specname, objects, reqs = read_this_scope(i,comments)
        if i_new <= i:
            raise RuntimeError('Developer Error, malformed file, or other generic bad behavior.')
        else:
            i = i_new
        if specname is None:
            specname = to_specname(name)
        specs.append((specname, objects, reqs))
    return specs
