"""rethink/known_specs.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Singleton dictionaries of specs used in factories.
"""
import os
import warnings

import collections
import copy

import rethink
import rethink.source_reader
import rethink.specs



class ConstValuedDict(collections.MutableMapping):
    """A dictionary that returns by copy to keep values pristine."""
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)

    def __getitem__(self, key):
        # includes specs we can learn on the fly
        if key.endswith("-list"):
            contained = self[key[:-len("-list")]]
            return rethink.specs.get_typed_list(key, contained, True)
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

# known_evaluators = ConstValuedDict()
# known_pks = ConstValuedDict()
# known_functions = ConstValuedDict()
# known_meshes = ConstValuedDict()
# known_solvers = ConstValuedDict()
# known_preconditioners = ConstValuedDict()

# def load_functions():
#     """Loads all function specs."""
#     global known_functions
    
#     path = os.path.join(rethink.AMANZI_SRC_DIR, "src", "functions")
#     for f in os.listdir(path):
#         if f.endswith("Function.hh") and not f == "Function.hh":
#             try:
#                 spec = rethink.source_reader.read(os.path.join(path,f))
#             except Exception as err:
#                 warnings.warn('Error reading "{0}": {1}'.format(f,err))
#             else:
#                 if len(spec) is 0:
#                     warnings.warn('Zero length spec "{0}"'.format(f))
                    
#                 else:
#                     specname = "function-" + f[:-len("Function.hh")].lower()
#                     known_functions[specname] = rethink.parameters.ParametersSpec(specname, spec)

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
    #print(inname,res)
    return res

def load_specs(path, warn_on_empty=False, warn_on_error=True):
    global known_specs

    # global type
    known_specs["list"] = rethink.specs.GenericList
    
    for dirname, subdirs, files in os.walk(path):
        for f in files:
            if f.endswith(".hh"):
                #try:
                print("Reading file: %s"%f)
                specs = rethink.source_reader.read(os.path.join(dirname,f))
                #except Exception as err:
                #    print("Error in file: %s"%f)
                #    #if warn_on_error:
                #    warnings.warn('Error reading "{0}": {1}'.format(os.path.join(dirname,f),err))
                #else:
                if True:
                    for specname, speclist, requirements in specs:
                        print("In file: %s got spec %s"%(f,specname))
                        if specname.endswith("-typed-spec"):
                            spec = rethink.specs.get_spec(specname, speclist, policy_spec_from_type="sublist", valid_types_by_name=None, evaluator_requirements=requirements)
                        elif specname.endswith("-typedinline-spec"):
                            spec = rethink.specs.get_spec(specname, speclist, policy_spec_from_type="flat list", valid_types_by_name=None, evaluator_requirements=requirements)
                        elif specname.endswith("-spec"):
                            spec = rethink.specs.get_spec(specname, speclist, evaluator_requirements=requirements)
                        else:
                            raise RuntimeError('Unrecognized spec "%s" from file "%s"'%(specname,f))
                        known_specs[specname] = spec
                    
    # now a second pass to clean up valid types
    for specname, spec in known_specs.items():
        if specname.endswith("-typed-spec") or specname.endswith("-typedinline-spec"):
            valids = dict()
            for name in spec.spec_notoneofs.keys():
                if name.endswith(" type"):
                    prefix = name[:-5]
                    prefix = prefix.replace(" ","-")+"-"
                    for k,v in known_specs.items():
                        if k.startswith(prefix):
                            valids[k] = v
            spec.valid_types = valids

    # now a third pass to set ptypes
    for specname, spec in known_specs.items():
        spec.set_ptype(known_specs)

    # do a pass to set key specs, which allow either suffix or key options
    try:
        print(known_specs["pk-physical-default-spec"].spec.keys())
        print(known_specs["pk-physical-default-spec"].spec_notoneofs.keys())
    except KeyError:
        pass
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
                    v = spec.spec_notoneofs.pop(k)
                    if v.default is not None and v.default.startswith("DOMAIN-"):
                        default = v.default[7:]
                    else:
                        default = None
                    assert(suffix not in spec.spec.keys())
                    spec.spec[suffix] = rethink.specs.PrimitiveParameter(suffix, str, default=default)
                    oneof = [[v,], [spec.spec[suffix],]]
                    spec.spec_oneofs.append(oneof)
                    spec.spec_oneof_inds.append(None)
                
                            

def load(warn_on_empty=False, warn_on_error=True):
    amanzi_path = os.path.join(rethink.AMANZI_SRC_DIR, "src")
    ats_path = os.path.join(rethink.ATS_SRC_DIR, "src")

    load_specs(amanzi_path, warn_on_empty, warn_on_error)
    load_specs(ats_path, warn_on_empty, warn_on_error)
    

def get_known_spec(name, typename):
    return rethink.specs.DerivedParameter(name, known_specs[typename])
