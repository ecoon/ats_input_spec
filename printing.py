"""rethink/printing.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Pretty printing.
"""

import rethink.colors
import rethink.primitives
import rethink.specs



def to_string(name, obj):
    """Single line string from name and object"""
    #print("entering help with: %r, %r"%(name, type(obj)))
    if type(obj) is rethink.specs.PrimitiveParameter:
        return obj.__str__()
    if type(obj) is rethink.specs.DerivedParameter:
        return obj.__str__()

    if rethink.primitives.is_primitive(type(obj)):
        return rethink.colors.NAME + name + rethink.colors.RESET + " = %r"%obj
    else:
        if obj.is_filled():
            if len(obj) > 0:
                filledstr = rethink.colors.FILLED + "Filled" + rethink.colors.RESET
            elif obj.cls.__name__.endswith("-list"):
                filledstr = rethink.colors.UNFILLED + "Empty List" + rethink.colors.RESET
            else:
                filledstr = rethink.colors.DEFAULT + "Defaults but Empty" + rethink.colors.RESET
        else:
            filledstr = rethink.colors.UNFILLED + "Not Filled" + rethink.colors.RESET
        return rethink.colors.NAME + name + rethink.colors.RESET + " [{0}] : {1}".format(obj.__name__, filledstr)

def _help(name, obj, include_optionals=True):
    #print("entering help with: %r, %r"%(name, type(obj)))
    try:
        isoptional = obj.is_optional()
    except AttributeError:
        isoptional = False

    try:
        isfilled = obj.is_filled()
    except AttributeError:
        isfilled = False

    header = to_string(name, obj)
    if not isfilled and isoptional:
        header += rethink.colors.DEFAULT + " [optional]" + rethink.colors.RESET
    #print("header (%s): %s"%(name, header))

    filled = []
    try:
        for k,v in obj.filled():
            filled.extend(_help(k,v,include_optionals))
    except AttributeError:
        pass
    unfilled = []
    try:
        for k,v in obj.unfilled():
            if type(v) is str:
                continue # this is the oneof meta-unfilled holder that should be removed
            unfilled.extend(_help(k,v,include_optionals))
    except AttributeError:
        pass

    if include_optionals:
        optionals = []
        try:
            for k,v in obj.optional():
                optionals.extend(_help(k,v,include_optionals))
        except AttributeError:
            pass

    try:
        oneofs = obj.oneofs()
    except AttributeError:
        oneofs = []
    oneof_lines = []
    for oneof in oneofs:
        if not include_optionals:
            print_this = True
            for opt in oneof:
                if all(obj.is_optional() for obj in opt):
                    print_this = False
                    break

        else:
            print_this = True
                    
        if print_this:
            oneof_lines.append("ONE OF:")
            for opts in oneof:
                oneof_lines.extend(["  "+l for opt in opts for l in _help(opt.name,opt,include_optionals)])
                oneof_lines.append("OR:")
            oneof_lines.pop()
        
    lines = [header,]
    if len(filled) > 0:
        #lines.append("  Filled:")
        lines.extend(["  "+u for u in filled])
    if len(unfilled) > 0:
        #lines.append("  Unfilled:")
        lines.extend(["  "+u for u in unfilled])
    if include_optionals and len(optionals) > 0:
        #lines.append("  Optional:")
        lines.extend(["  "+u for u in optionals])
    if len(oneof_lines) > 0:
        lines.extend(["  "+u for u in oneof_lines])

    #print("Exiting with lines (%s): %r"%(name,'\n'.join(lines)))
    return lines
        

def help(name, obj, optional=True):
    lines = _help(name, obj, optional)
    print('\n'.join(lines))

        
    

