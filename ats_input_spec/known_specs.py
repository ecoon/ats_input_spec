"""ats_input_spec/known_specs.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Singleton dictionaries of specs used in factories.
"""
import os
import warnings
import logging

import collections.abc
import copy

import ats_input_spec
import ats_input_spec.source_reader
import ats_input_spec.specs

class ConstValuedDict(collections.abc.MutableMapping):
    """A dictionary that returns by copy to keep values pristine.  

    UMMMM This isn't true?
    """
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self['list'] = ats_input_spec.specs.GenericList

    def __getitem__(self, key):
        # includes specs we can learn on the fly
        if key.endswith('-list'):
            contained = self[key[:-len('-list')]]
            return ats_input_spec.specs.get_typed_list(key, contained)
        else:
            return self._store[key]
            
    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __delitem__(self, key):
        del self._store[key]    
                    
    def __setitem__(self, key, value):
        self._store[key] = value
        

known_specs = ConstValuedDict()

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

def _load_specs_from_lines(name, lines):
    """Private load, use the public one instead."""
    global known_specs

    specs = ats_input_spec.source_reader.read_lines(name, lines)

    for specname, speclist, requirements in specs:
        logging.debug("In file: %s got spec %s"%(name,specname))
        if specname.endswith("-typed-spec"):
            spec = ats_input_spec.specs.get_spec(specname, speclist, policy_spec_from_type="standard", valid_types_by_name=None, evaluator_requirements=requirements)
        elif specname.endswith("-typedinline-spec"):
            spec = ats_input_spec.specs.get_spec(specname, speclist, policy_spec_from_type="flat list", valid_types_by_name=None, evaluator_requirements=requirements)
        elif specname.endswith("-typedsublist-spec"):
            spec = ats_input_spec.specs.get_spec(specname, speclist, policy_spec_from_type="sublist", valid_types_by_name=None, evaluator_requirements=requirements)
        elif specname.endswith("-spec"):
            spec = ats_input_spec.specs.get_spec(specname, speclist, evaluator_requirements=requirements)
        else:
            raise RuntimeError('Unrecognized spec "%s" from file "%s"'%(specname,name))
        known_specs[specname] = spec

    return len(specs)

def load_specs_from_lines(name, lines, on_error='error'):
    """Load specs from a collection of lines."""
    if on_error == None:
        try:
            return _load_specs_from_lines(name, lines)
        except Exception:
            pass
    elif on_error == 'warn':
        try:
            return _load_specs_from_lines(name, lines)
        except Exception as e:
            warning.warning(f'Failed loading from "{name}" with error:')
            warning.warning(f'{e}')
    elif on_error == 'error':
        return _load_specs_from_lines(name, lines)
    else:
        raise ValueError('Invalid value for on_error')

    

def load_specs(path, on_empty=None, on_error=None):
    global known_specs
    
    for dirname, subdirs, files in os.walk(path):
        for f in files:
            if f.endswith(".hh") and not f.endswith("_reg.hh"):
                logging.debug("Reading file: %s"%f)
                with open(os.path.join(dirname,f), 'r') as fid:
                    lines = ats_input_spec.source_reader.find_all_comments(fid)
                count = load_specs_from_lines(f[:-3], lines, on_error)
                if count == 0:
                    if on_error == 'warn':
                        warning.warning(f'load of "{f[:-3]}" resulted in no specs')
                    elif on_error == 'error':
                        raise RuntimeError(f'load of "{f[:-3]}" resulted in no specs')

def load_selected_specs(path, selected, on_empty=None, on_error=None):
    global known_specs

    l_selected = selected.copy()
    for dirname, subdirs, files in os.walk(path):
        for f in files:
            if f.endswith(".hh") and os.path.split(f)[-1][:-3] in selected:
                l_selected.remove(os.path.split(f)[-1][:-3])
                print("Reading file: %s"%f)
                with open(os.path.join(dirname,f), 'r') as fid:
                    lines = ats_input_spec.source_reader.find_all_comments(fid)
                load_specs_from_lines(f[:-3], lines)
    return l_selected

def finish_load():
    global known_specs

    # set valid types for typed specs
    for specname, spec in known_specs.items():
        if specname.endswith("-typed-spec") or \
           specname.endswith("-typedinline-spec"):
            valids = dict()
            for name in spec.spec_others.keys():
                if name.endswith(" type"):
                    prefix = name[:-5]
                    prefix = prefix.replace(" ","-")+"-"
                    for k,v in known_specs.items():
                        if k.startswith(prefix):
                            valids[k] = v
            spec.valid_types = valids
        elif specname.endswith("-typedsublist-spec"):
            valids = dict()
            prefix = specname[:-len("-typedsublist-spec")]
            for k,v in known_specs.items():
                if k.startswith(prefix) and k not in [f'{prefix}-typedsublist-spec',
                                                      f'{prefix}-typedsublist-spec-list',
                                                      f'{prefix}-spec']:
                    valids[k] = v
            spec.valid_types = valids

    # set ptypes
    for specname, spec in known_specs.items():
        spec.set_ptype(known_specs)

    # set key specs, which allow either suffix or key options
    for specname, spec in known_specs.items():
        try:
            spec_keys = list(spec.spec.keys()) # copy to modify
        except AttributeError: # not a spec
            pass
        else:
            for k in spec_keys:
                if k.endswith(" key"):
                    base = k[:-4]
                    suffix = base + " suffix"
                    v = spec.spec_others.pop(k)
                    if v.default is not None and v.default.startswith("DOMAIN-"):
                        default = v.default[7:]
                    else:
                        default = None
                    assert(suffix not in spec.spec.keys())
                    spec.spec[suffix] = ats_input_spec.specs.PrimitiveParameter(suffix, str, default=default)
                    oneof = [[v,], [spec.spec[suffix],]]
                    spec.spec_oneofs.append(oneof)
                    spec.spec_oneof_inds.append(None)
                
                            
def load(on_empty=None, on_error='warn'):
    amanzi_path = os.path.join(ats_input_spec.AMANZI_SRC_DIR, "src")
    load_specs(amanzi_path, on_empty, on_error)
    finish_load()

def load_selected(files, on_empty=None, on_error=None):
    amanzi_path = os.path.join(ats_input_spec.AMANZI_SRC_DIR, "src")
    load_selected_specs(amanzi_path, files, on_empty, on_error)
    finish_load()
    
def clear():
    global known_specs
    known_specs = ConstValuedDict()

    
def get_known_spec(name, typename):
    return ats_input_spec.specs.DerivedParameter(name, known_specs[typename])


# global singleton dictionary of known specs, either pre-loaded or loaded on demand
known_specs = ConstValuedDict()
known_specs["list"] = ats_input_spec.specs.GenericList

