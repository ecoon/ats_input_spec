"""ats_input_spec/specs.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Definitions of types that are collections of other parameters.

"""
import collections.abc
import ats_input_spec.primitives
import ats_input_spec.colors
import ats_input_spec.printing
import copy
import warnings

class PrimitiveParameter(object):
    """A parameter whose type is a primitive."""
    def __init__(self, name, ptype, default=None, optional=False):
        self.name = name
        self.ptype = ptype
        self.default = default

        if self.default is not None or optional:
            self._optional = True
        else:
            self._optional = False

    def __str__(self):
        """name [type] = default (optional)

          OR

        name [type] (optional)
        """
        namestring = ats_input_spec.colors.NAME + self.name + ats_input_spec.colors.RESET
        typestring = ats_input_spec.primitives.print_primitive_type(self.ptype)

        if self.default is not None:
            defaultstring = "= %r"%self.default
        elif self.is_optional():
            defaultstring = "= None"
        else:
            defaultstring = "= " + ats_input_spec.colors.UNFILLED + "None" + ats_input_spec.colors.RESET

        # optionalstring = ""
        # if self.is_optional():
        #     optionalstring = ats_input_spec.colors.DEFAULT + "(optional)" + ats_input_spec.colors.RESET
        # return "%s [%s] %s %s"%(namestring,typestring,defaultstring,optionalstring)
        return "%s [%s] %s"%(namestring,typestring,defaultstring)
        
    def is_optional(self):
        return self._optional

    def set_ptype(self, known_types):
        assert(type(self.ptype) is type)

    
class DerivedParameter(object):
    """A parameter whose type is a derived object."""
    def __init__(self, name, ptype, optional=False):
        self.name = name
        self.ptype = ptype
        self._optional = optional

    def __str__(self):
        """name [type] = default (optional)

          OR

        name [type] (optional)
        """
        namestring = ats_input_spec.colors.NAME + self.name + ats_input_spec.colors.RESET

        if type(self.ptype) is str:
            typestring = self.ptype
        else:
            typestring = "%s"%self.ptype.__name__
        # optionalstring = ""
        # if self.is_optional():
        #     optionalstring = ats_input_spec.colors.DEFAULT + "(optional)" + ats_input_spec.colors.RESET
        # return "%s [%s] %s %s"%(namestring,typestring,defaultstring,optionalstring)
        return "%s [%s]"%(namestring,typestring)

    def is_optional(self):
        return self._optional

    def set_ptype(self, known_types):
        if type(self.ptype) is str:
            self.ptype = known_types[self.ptype]
    

def _flatten(container):
    """simple flatten"""
    for i in container:
        if isinstance(i, (list,tuple)):
            for j in _flatten(i):
                yield j
        else:
            yield i
    

class GenericList(collections.abc.MutableMapping):
    __name__ = "list"
    """Base class for specs."""
    def __init__(self):
        self._store = dict()

    # things to shut up ABC 
    def __getitem__(self, key):
        return self._store[key]
    
    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __delitem__(self, key):
        del self._store[key]    
                    
    def __setitem__(self, key, value):
        self._store[key] = value

    def is_filled(self):
        """Is this list potentially complete?"""
        for k,v in self.items():
            if v is None:
                return False
            elif not ats_input_spec.primitives.is_primitive(type(v)) and not v.is_filled():
                return False
        return True

    def filled(self):
        """Returns a generator to (name,value) pairs of filled objects in the spec."""
        # parameters that are set and filled
        for k,v in self._store.items():
            if v is not None:
                if ats_input_spec.primitives.is_primitive(type(v)):
                    yield k,v
                elif v.is_filled():
                    yield k,v

    def unfilled(self):
        """Returns a generator to (name, value) or (name,ptype) or (oneof_#, oneof_#) 
        pairs of unfilled objects or unselected oneof branches in the
        spec."""
        # parameters that are set but not filled
        for k,v in self.items():
            if v is None:
                yield k,v
            else:
                if not ats_input_spec.primitives.is_primitive(type(v)) and not v.is_filled():
                    yield k,v

    @classmethod
    def set_ptype(cls, known_types):
        pass

#
# Class and contructors for a list with a type
class _TypedList(GenericList):
    def append_empty(self, name):
        """Append an empty object of type given by my type to the list.

        Typed objects change their own spec.  To do this without
        affecting all others, we have to create a new class for each one.
        """
        assert(name not in self.keys())
        if self._primitive:
            self.__setitem__(name, None)
            return None
        else:
            self.__setitem__(name,copy_spec(self.ContainedPType)())
            return self[name]

    def __setitem__(self, key, value):
        if self._primitive:
            value = ats_input_spec.primitives.valid_from_type(self.ContainedPType, value)
        super(_TypedList,self).__setitem__(key, value)

    def is_filled(self):
        """Is this list potentially complete?"""
        if len(self) == 0:
            return self._empty_policy
        else:
            return super(_TypedList,self).is_filled()
        
    def unfilled(self):
        """Returns a generator to (name, value) or (name,ptype) or (oneof_#, oneof_#) 
        pairs of unfilled objects or unselected oneof branches in the
        spec."""
        # if the list is empty, need at least one item
        for k,v in super(_TypedList,self).unfilled():
            yield k,v

    @classmethod
    def set_ptype(cls, known_types):
        if type(cls.ContainedPType) is str:
            cls.ContainedPType = known_types[cls.ContainedPType]

            
def get_typed_list(name, ptype, empty_policy=False):
    """Generates a spec for a Typed List.

    Argument:
      ptype             | A single type for which this list contains.
      empty_policy      | Can the list be empty?

    Returns:
      A class for a list of that type.
    """
    class _MyTypedList(_TypedList):
        """A list whose entries must be of a given type."""
        ContainedPType = ptype
        _primitive = ats_input_spec.primitives.is_primitive(ptype)
        _empty_policy = empty_policy
        __name__ = name

    _MyTypedList.__name__ = name
            
    return _MyTypedList


#
# Class and contructors for a specced set of paramters.
class _Spec(GenericList):
    def __init__(self):
        super(_Spec,self).__init__()
        for k,p in self.spec_others.items():
            if not p.is_optional() and not ats_input_spec.primitives.is_primitive(p.ptype):
#            if not p.is_optional():
                self.fill_default(k)
    
    def is_filled(self):
        """Is this spec potentially complete?"""
        for k,v in self.items():
            if v is None:
                return False
            elif not ats_input_spec.primitives.is_primitive(type(v)) and not v.is_filled():
                return False
        for k,p in self.spec_others.items():
            if not (k in self.keys() or p.is_optional()):
                return False
        for i,oneof in enumerate(self.spec_oneofs):
            if self.spec_oneof_inds[i] is None:
                return False
            else:
                any_full = False
                for j in self.spec_oneof_inds[i]:
                    if all((opt.is_optional() or opt.name in self.keys()) for opt in self.spec_oneofs[i][j]):
                        any_full = True
                        break
                if not any_full:
                    return False

        # nothing special to do for conditionals        
        return True

    def fill_default(self, name):
        """Create an empty container for the contained spec given by name."""
        p = self.spec[name]
        if ats_input_spec.primitives.is_primitive(p.ptype):
            if p.default is not None:
                self[name] = p.default
            else:
                self[name] = None
        else:
            self[name] = p.ptype()
        return self[name]

    def __getitem__(self, key):
        return super(_Spec,self).__getitem__(key)

    def _setitem(self, name, ptype, value):
        """Set the item without asking questions.  Used internally only!"""
        if ats_input_spec.primitives.is_primitive(ptype):
            value = ats_input_spec.primitives.valid_from_type(ptype, value)
        super(_Spec,self).__setitem__(name, value)
        
    def __setitem__(self, name, value):
        try:
            pp = self.spec[name]
        except KeyError:
            # not in the spec
            if self._policy_not_in_spec == "error":
                print('Parameter "%s" is not in the spec.'%(name))
                ats_input_spec.printing.help("", self)
                raise KeyError('Parameter "%s" is not in the spec.'%(name))
            elif self._policy_not_in_spec == "warn":
                warnings.warn("Adding parameter %s of type %r even though it is not in the spec."%(name, type(value)))
                super(_Spec,self).__setitem__(name, value)
            else:
                super(_Spec,self).__setitem__(name, value)
                
        else:
            if name not in self.spec_others.keys():
                # requested a parameter that is not in the other list
                # check if it is in a THEN or ELSE block and error about setting the conditional
                for j, conditional in enumerate(self.spec_conditionals):
                    cond = conditional[0]
                    if name == cond.name:
                        assert(type(value) is bool)
                    
                    for i, opt in enumerate(conditional[1]):
                        if name in (p.name for p in opt):
                            if cond.value == True:
                                pass
                            elif cond.value == False:
                                raise RuntimeError('Attempting to set a parameter in a THEN '
                                                   'block but the conditional was set to FALSE: "{cond.name}"')
                            else:
                                raise RuntimeError('Attempting to set a parameter in a THEN '
                                                   'block without first setting the IF block '
                                                   'conditional value to TRUE: "{cond.name}"')
                            
                    for i, opt in enumerate(conditional[2]):
                        if name in (p.name for p in opt):
                            if cond.value == False:
                                pass
                            elif cond.value == True:
                                raise RuntimeError('Attempting to set a parameter in an ELSE '
                                                   'block but the conditional was set to TRUE: "{cond.name}"')
                            else:
                                raise RuntimeError('Attempting to set a parameter in an ELSE '
                                                   'block without first setting the IF block '
                                                   'conditional value to FALSE: "{cond.name}"')
            
                # check if in a oneof
                for j,oneof in enumerate(self.spec_oneofs):
                    matches = []
                    for i,opt in enumerate(oneof):
                        if name in (p.name for p in opt):
                            matches.append(i)

                    if len(matches) == 0:
                        pass
                    elif len(matches) == 1:
                        if self.spec_oneof_inds[j] is not None and matches[0] not in self.spec_oneof_inds[j]:
                            raise RuntimeError('Spec with oneof including "%s" requested entries of a different branch.')
                        self.spec_oneof_inds[j] = matches
                    elif len(matches) > 1:
                        if self.spec_oneof_inds[j] is not None:
                            self.spec_oneof_inds[j] = list(set(self.spec_oneof_inds[j]).intersection(set(matches)))
                            if len(self.spec_oneof_inds[j]) == 0:
                                raise RuntimeError('Spec with oneof including "%s" requested entries of a different branch.')
                        else:
                            self.spec_oneof_inds[j] = matches

            # check if a type
            if self._policy_spec_from_type is not None and name.endswith(" type"):
                assert(type(value) is str)
                typename = name[0:-len(" type")]

                # add subspec info
                subspec_name = value+" parameters"
                subspec_specname = (typename+" "+value).replace(" ","-")+"-spec"
                try:
                    subspec_ptype = self.valid_types[subspec_specname]
                except KeyError:
                    raise KeyError('Typed spec "%s" with value "%s" does not have a valid spec for "%s"'%(name,value,subspec_specname))
                else:
                    if self._policy_spec_from_type == "sublist":
                        self.spec_others[subspec_name] = DerivedParameter(subspec_name, subspec_ptype, False)
                        self.spec[subspec_name] = self.spec_others[subspec_name]
                        self.fill_default(subspec_name)
                    elif self._policy_spec_from_type == "flat list":
                        for k,v in subspec_ptype.spec_others.items():
                            self.spec_others[k] = v
                        for k,v in subspec_ptype.spec.items():
                            self.spec[k] = v
                        self.spec_oneofs.extend(subspec_ptype.spec_oneofs)
                        self.spec_oneof_inds.extend(subspec_ptype.spec_oneof_inds)
                            
            # insert it already                
            self._setitem(name, pp.ptype, value)


    def unfilled(self):
        """Returns a generator to (name, value) or (name,ptype) or (oneof_#, oneof_#) 
        pairs of unfilled objects or unselected oneof branches in the
        spec."""
        for k,v in super(_Spec,self).unfilled():
            yield k,v
        # non-optional parameters not yet set/filled
        for k,v in self.spec_others.items():
            if k not in self.keys() and not v.is_optional():
                yield k,v
        # non-optional parameters in selected oneof branches
        for i,oneofs in enumerate(self.spec_oneofs):
            if self.spec_oneof_inds[i] is None or len(self.spec_oneof_inds[i]) > 1:
                yield "one_of %r"%i, "one_of %r"%i
            else:
                for opt in oneofs[self.spec_oneof_inds[i][0]]:
                    if opt.name not in self.keys() and not opt.is_optional():
                        yield opt.name, opt
        # conditionals
        for i,cond in enumerate(self.spec_conditionals):
            if cond[0][0].name not in self.keys() and not cond[0][0].is_optional():
                yield "if conditional %r"%i, "if conditional %r"%i
            else:
                k = cond[0][0].name
                if k in self.keys():
                    v = self[k].value
                else:
                    v = cond[0][0].default
                if v == True:
                    for opt in cond[1]:
                        if opt.name not in self.keys() and not opt.is_optional():
                            yield opt.name, opt
                elif v == False:
                    for opt in cond[2]:
                        if opt.name not in self.keys() and not opt.is_optional():
                            yield opt.name, opt

                        
    def optional(self):
        """Returns a generator to (name, ptype) optional (but not filled) parameters."""
        # optional parameters not yet set/filled
        for k,v in self.spec_others.items():
            if k not in self.keys() and v.is_optional():
                yield k,v

        # optional parameters in selected oneof branches
        for i,oneofs in enumerate(self.spec_oneofs):
            if self.spec_oneof_inds[i] is not None and len(self.spec_oneof_inds[i]) == 1:
                for p in oneofs[self.spec_oneof_inds[i][0]]:
                    if p.name not in self.keys() and p.is_optional():
                        yield p.name, p

        # conditionals
        for i,cond in enumerate(self.spec_conditionals):
            if cond[0][0].name not in self.keys() and cond[0][0].is_optional():
                yield cond[0][0].name, cond[0][0]
            elif cond[0][0].name in self.keys():
                v = self[k].value
                if v == True:
                    for opt in cond[1]:
                        if opt.name not in self.keys() and opt.is_optional():
                            yield opt.name, opt
                elif v == False:
                    for opt in cond[2]:
                        if opt.name not in self.keys() and opt.is_optional():
                            yield opt.name, opt
                        
                
    def oneofs(self):
        """List of undetermined oneofs, each of which is a list of untrimmed branches of that oneof.

        Note, unlike the others, this is not a generator!
        """
        ret = list()
        for i,oneofs in enumerate(self.spec_oneofs):
            if self.spec_oneof_inds[i] is None:
                available = range(len(oneofs))
            elif len(self.spec_oneof_inds[i]) > 1:
                available = self.spec_oneof_inds[i]
            else:
                available = None

            if available is not None:
                oneof = list()
                for a in available:
                    opt = list()
                    for p in oneofs[a]:
                        if p.name not in self.keys():
                            opt.append(p)
                    oneof.append(opt)
                ret.append(oneof)
        return ret

    @classmethod
    def set_ptype(cls, known_types):
        to_remove = []
        for include in cls.includes:
            # an include
            include_ptype = include[0]
            to_add = known_types[include_ptype]
            for newk,v in to_add.spec_others.items():
                cls.spec_others[newk] = v
            for newk,v in to_add.spec.items():
                cls.spec[newk] = v
            cls.spec_oneofs.extend(to_add.spec_oneofs)
            cls.spec_oneof_inds.extend(to_add.spec_oneof_inds)
            cls.option_keys.extend(to_add.option_keys)
            cls.eval_reqs.extend(to_add.eval_reqs)

            # Modifying this list while looping over it is dangerous,
            # but may be ok?  We don't really want to make a copy, but
            # want to recursively include our included spec's
            # includes.
            cls.includes.extend(to_add.includes)
                
        for k,v in cls.spec.items():
            v.set_ptype(known_types)


class Conditional(list):
    """Dummy class for naming conditionals"""
    pass

class OneOfList(list):
    """Dummy class for naming OneOf parameters"""
    pass
    
class _TypedSpec(_Spec):
    def __init__(self):
        super(_Spec,self).__init__()

    def __setitem__(self, name, value):
        if name.endswith(" type"):
            self.set_type(name[:-len(" type")], value)
        else:
            super(_TypedSpec, self).__setitem__(name, value)

    def set_type(self, name, value):
        subspec_specname = "{}-{}-spec".format(name,value).replace(" ","-").replace("_","-")
        try:
            subspec_ptype = self.valid_types[subspec_specname]
        except KeyError:
            raise KeyError('Typed spec "%s" with value "%s" does not have a valid spec for "%s"'%(name,value,subspec_specname))

        # add subspec info
        if self._policy_spec_from_type == "standard":
            subspec_name = "{} parameters".format(value)
            self.spec_others[subspec_name] = DerivedParameter(subspec_name, subspec_ptype, False)
            self.spec[subspec_name] = self.spec_others[subspec_name]
            self.fill_default(subspec_name)
            super(_TypedSpec, self).__setitem__(name+" type", value)

        elif self._policy_spec_from_type == "flat list":
            for k,v in subspec_ptype.spec_others.items():
                self.spec_others[k] = v
            for k,v in subspec_ptype.spec.items():
                self.spec[k] = v
            self.spec_oneofs.extend(subspec_ptype.spec_oneofs)
            self.spec_oneof_inds.extend(subspec_ptype.spec_oneof_inds)
            super(_TypedSpec, self).__setitem__(name+" type", value)

        elif self._policy_spec_from_type == "sublist":
            subspec_name = "{}: {}".format(name, value)
            self.spec_others[subspec_name] = DerivedParameter(subspec_name, subspec_ptype, False)
            self.spec[subspec_name] = DerivedParameter(subspec_name, subspec_ptype, False) 
            self.fill_default(subspec_name)

        else:
            raise ValueError("Unknown typed policy type: {}".format(self._policy_spec_from_type))

    def get_sublist(self, name):
        if self._policy_spec_from_type == "standard":
            value = self[name+" type"]
            return self[value+" parameters"]
        elif self._policy_spec_from_type == "flat list":
            return self
        elif self._policy_spec_from_type == "sublist":
            assert(len(self) == 1)
            return list(self.values())[0]

        else:
            raise ValueError("Unknown typed policy type: {}".format(self._policy_spec_from_type))


def get_spec(name, list_of_parameters, others=None,
             policy_not_in_spec="error", policy_spec_from_type=None,
             valid_types_by_name=None):
    """Generates a spec for a list of parameters, including optional and 
    defaulted parameters, which may be primitive or derived types.

    Arguments
    ---------
    name : str
      Name of the spec.
    list_of_parameters : list
      List of PrimitiveParameter or DerivedParameter objects.
    others : tuple
      require_evaluators, keys, includes.  Each are lists.
    policy_not_in_spec : str, optional (None)
      If a value is requested that is not in the spec, respond by
      'error', 'warn', or 'none'
    policy_spec_from_type : str, optional (None)
      Where to specify the "type" of a typed object.  Either
      "standard", "flat list", or "sublist" (or "none"/None).
    valid_types_by_name : list, optional (None)
      Not used currently, will be used to specify the valid types.

    Returns:
      A class for a spec including these parameters.

    """
    if others is None:
        evaluators_required = []
        opt_keys = []
        include_others = []
    else:
        assert(type(others) in [list,tuple])
        assert(len(others) == 3)
        (evaluators_required, opt_keys, include_others) = others

    if valid_types_by_name is None:
        valid_types_by_name = dict()

    if (policy_spec_from_type is None or policy_spec_from_type == "none"):
        class _MySpec(_Spec):
            """A spec, or list of requirements to fill an input parameter set."""
            spec = {p.name:p for p in _flatten(list_of_parameters)}
            spec_others = {p.name:p for p in list_of_parameters if type(p) not in [OneOfList, Conditional]}
            spec_oneofs = [p for p in list_of_parameters if type(p) is OneOfList]
            spec_conditionals = [p for p in list_of_parameters if type(p) is Conditional]
            spec_oneof_inds = [None for i in range(len(spec_oneofs))]
            _policy_not_in_spec = policy_not_in_spec
            _policy_spec_from_type = None
            valid_types = valid_types_by_name
            eval_reqs = evaluators_required
            option_keys = opt_keys
            includes = include_others
            __name__ = name

    else:
        class _MySpec(_TypedSpec):
            """A spec, or list of requirements to fill an input parameter set."""
            spec = {p.name:p for p in _flatten(list_of_parameters)}
            spec_others = {p.name:p for p in list_of_parameters if type(p) not in [OneOfList, Conditional]}
            spec_oneofs = [p for p in list_of_parameters if type(p) is OneOfList]
            spec_conditionals = [p for p in list_of_parameters if type(p) is Conditional]
            spec_oneof_inds = [None for i in range(len(spec_oneofs))]
            _policy_not_in_spec = policy_not_in_spec
            _policy_spec_from_type = policy_spec_from_type
            valid_types = valid_types_by_name
            eval_reqs = evaluators_required
            option_keys = opt_keys
            includes = include_others
            __name__ = name
        
    _MySpec.__name__ = name
    return _MySpec


def copy_spec(spec):
    """Some specs modify themselves in-place, meaning that we need a fresh one of them to avoid breaking all others.

    This literally copies the class, creating a new class with the same class variables.
    """
    name = spec.__name__
    list_of_parameters = list(spec.spec.values())
    valid_types_by_name = copy.copy(spec.valid_types)
    evaluator_requirements = copy.copy(spec.eval_reqs)
    opt_keys = copy.copy(spec.option_keys)
    include_others = copy.copy(spec.includes)
    others = (evaluator_requirements, opt_keys, include_others)

    try:
        policy_spec_from_type = spec._policy_spec_from_type
    except AttributeError:
        policy_spec_from_type = None
        
    return get_spec(spec.__name__, list_of_parameters, others,
                    spec._policy_not_in_spec, policy_spec_from_type,
                    valid_types_by_name)
    


