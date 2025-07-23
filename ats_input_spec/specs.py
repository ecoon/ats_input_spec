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
import itertools

DELIMITER = '-'


class Parameter(object):
    """An entry, consisting of a name, type, metadata, and value."""
    def __init__(self, name, ptype=None, default=None, optional=False, value=None):
        self.name = name

        # set the paramter type
        if ptype in ats_input_spec.primitives.valid_types:
            # this is a primitive type
            self._primitive = True
            self.ptype_string = ats_input_spec.primitives.primitives_to_text[ptype]
            self.ptype = ptype
        elif type(ptype) is str:
            # this is a derived type, and the class spec is not yet assigned
            self._primitive = False
            self.ptype_string = ptype
            self.ptype = ptype
        elif ptype is None:
            # derived type, and the class spec is being assigned here as value
            assert(value is not None)
            self._primitive = False
            self.ptype_string = str(self._primitive)
            self.ptype = None
        else:
            # derived type with unknown typename
            self._primitive = False
            self.ptype_string = 'unknown derived parameter'
            self.ptype = ptype

        # validate and assign default
        if default is not None:
            assert(self._primitive)
            default = ats_input_spec.primitives.valid_from_type(self.ptype, default)
        self.default = default

        # set _optional flag
        if self.default is not None or optional:
            self._optional = True
        else:
            self._optional = False
        
        # validate and assign value
        if value is not None:
            if self._primitive:
                value = ats_input_spec.primitives.valid_from_type(self.ptype, value)
        self.value = value

    def _name_string(self):
        return ats_input_spec.colors.NAME + self.name + ats_input_spec.colors.RESET

    def _value_string(self):
        if self.is_primitive():
            val = self.get()
            if val is not None:
                return ats_input_spec.primitives.string_from_primitive(val)
            elif self.is_optional():
                return "[optional]"
            else:
                return ats_input_spec.colors.UNFILLED + "None" + ats_input_spec.colors.RESET
        else:
            if self.value is None or not self.value.is_complete():
                return ats_input_spec.colors.UNFILLED + "[incomplete]" + ats_input_spec.colors.RESET
            else:
                if self.value.is_optional() and not self.value.has_value():
                    return "[optional]"
                else:
                    return ats_input_spec.colors.FILLED + "[complete]" + ats_input_spec.colors.RESET

    def __repr__(self):
        return "Parameter(%r, ptype=%s, default=%r, optional=%r, value=%r)"%(self.name, self.ptype, self.default, self._optional, self.value)
    
    def __str__(self):
        header = "%s [%s] : %s"%(self._name_string(), self.ptype_string, self._value_string())
        if not self.is_primitive() and self.get() is not None:
            header = header + '\n' + ats_input_spec.colors.indent(str(self.get()))
        return header

    def __getitem__(self, k):
        """Passthrough to the value"""
        assert(not self.is_primitive())
        assert(self.value is not None)
        return self.value[k]

    def __setitem__(self, k, v):
        """Passthrough to the value"""
        assert(not self.is_primitive())
        assert(self.value is not None)
        self.value[k] = v
    
    
    def set(self, value):
        """Sets value with type checking."""
        if self.is_primitive():
            self.value = ats_input_spec.primitives.valid_from_type(self.ptype, value)
        else:
            # no type checking to be done
            self.value = value

    def get(self):
        """Gets a value, substituting the default."""
        if self.value is not None:
            return self.value
        elif self.default is not None:
            return self.default
        else:
            return None

    def is_primitive(self):
        """Is this a plain-old-data type?"""
        return self._primitive

    def is_optional(self):
        """Must this be provided in a complete spec?"""
        return self._optional

    def has_value(self):
        """Has a value been set (and therefore this needs to be written)?"""
        if self.is_primitive():
            return self.value is not None
        else:
            return self.value is not None and self.value.has_value()

    def is_complete(self):
        """Can this be written now and result in a valid run?"""
        if self.is_primitive():
            return self.is_optional() or self.has_value()
        else:
            return self.is_optional() or \
                (self.value is not None and self.value.is_complete())

    def copy(self):
        """A deep copy of self"""
        if self.is_primitive():
            return Parameter(self.name, self.ptype, self.default,
                             self._optional, self.value)
        else:
            if self.value is not None:
                new_val = self.value.copy()
            else:
                new_val = None
            return Parameter(self.name, self.ptype, self.default,
                             self._optional, new_val)



class ParameterCollection(collections.abc.MutableMapping):
    """A collection of parameters, this class acts like a dictionary from name : value.

    But it is actually a dictionary from name : Parameter instances!
    """
    def __init__(self, pars=None, policy_not_in_spec='error', policy_empty_is_complete=False):
        if type(pars) in [list,tuple]:
            pars = dict((p.name, p) for p in pars)
        elif pars is None:
            pars = dict()
        assert(type(pars) is dict)
        self._pars = pars # a dictionary from name : Parameter object.
        self._policy_not_in_spec = policy_not_in_spec
        self._policy_empty_is_complete = policy_empty_is_complete

    # things to shut up ABC 
    def __getitem__(self, k):
        return self._pars[k].get()
    
    def __iter__(self):
        return iter(self._pars)

    def __len__(self):
        return len(self._pars)

    def __delitem__(self, k):
        del self._pars[k]    
                    
    def __setitem__(self, k, v):
        if k not in self._pars:
            if self._policy_not_in_spec == 'warn' :
                warnings.warn(f'Adding parameter {k} of type {type(v)} to the spec.')
            elif self._policy_not_in_spec == 'error':
                raise KeyError(f'Parameter "{k}" is not in the Collection.')
            self._pars[k] = Parameter(k, type(v), value=v)
        else:
            self._pars[k].set(v)

    def __contains__(self, k):
        return k in self._pars

    def __str__(self):
        return '\n'.join(['%s'%p for p in self._pars.values()])
    
    def parameters(self):
        """Generator for all parameter objects."""
        for p in self._pars.values():
            yield p
                
    def get_parameter(self, k):
        """Accessor for a parameter object."""
        return self._pars[k]

    def is_complete(self):
        """Does this collection consist of all complete objects?"""
        if len(self) == 0:
            return self._policy_empty_is_complete
        return all(p.is_complete() for p in self._pars.values())

    def complete(self):
        """Generator for all entries that are complete."""
        for p in self._pars.values():
            if p.is_complete():
                yield p

    def has_value(self):
        return any(p.has_value() for p in self._pars.values())

    def valued(self):
        """Generator for all entries that has_value()"""
        for p in self._pars.values():
            if p.has_value():
                yield p

    def is_optional(self):
        return all(p.is_optional() for p in self._pars.values())
                
    def copy(self):
        pardict = dict((k,v.copy()) for (k,v) in self._pars.items())
        return ParameterCollection(pardict, self._policy_not_in_spec)

    # def append_empty(self, k, v):
    #     self._pars[k] = v


class Spec(collections.abc.MutableSequence):
    """A collection of Collections, this defines a spec."""
    def __init__(self, iterable=None, policy_empty_is_complete=False, **kwargs):
        if iterable is None:
            iterable = list()

        self.collections = list(iterable)
        self._policy_empty_is_complete = policy_empty_is_complete

        if 'dependencies' in kwargs:
            self.dependencies = kwargs['dependencies']
        else:
            self.dependencies = list()
        if 'keys' in kwargs:
            self.keys = kwargs['keys']
        else:
            self.keys = list()
        if 'evaluators' in kwargs:
            self.evaluators = kwargs['evaluators']
        else:
            self.evaluators = list()
        if 'includes' in kwargs:
            self.includes = kwargs['includes']
        else:
            self.includes = list()

    def __getitem__(self, i):
        if type(i) is int:
            return self.collections[i]
        else:
            try:
                return next(c[i] for c in self.collections if i in c)
            except StopIteration:
                raise KeyError(f'Spec does not have parameter entry {i}')

    def _find_key(self, k):
        """A private implementation that returns the index of the branch."""
        # search for the containing branch and set the value
        try:
            index = next(j for (j,coll) in enumerate(self.collections) if k in coll)
        except StopIteration:
            raise KeyError(f'Parameter "{k}" is not in the {__name__}')
        else:
            return index
            
    def __setitem__(self, i, value):
        if type(i) is int:
            assert(iter(value) is not None)
            self.collections[i] = value
        else:
            index = self._find_key(i)
            self.collections[index][i] = value

    def __delitem__(self, i):
        if type(i) is int:
            self.collections.__delitem__(i)
        elif type(i) is str:
            next(coll for coll in self.collections if i in coll).__delitem__(i)

    def __len__(self):
        return len(self.collections)

    def insert(self, i, value):
        self.collections.insert(i, value)
        
    def __contains__(self, k):
        return any((k in coll) for coll in self.collections)

    def __str__(self):
        return '\n'.join(['%s'%coll for coll in self.collections])
    
    def parameters(self):
        for collection in self.collections:
            for p in collection.parameters():
                yield p

    def is_complete(self):
        if len(self) == 0:
            return self._policy_empty_is_complete
        return all(coll.is_complete() for coll in self.collections)

    def complete(self):
        """Generator for complete parameters."""
        for coll in self.collections:
            for p in coll.complete():
                yield p

    def has_value(self):
        return any(coll.has_value() for coll in self.collections)

    def valued(self):
        """Generator for parameters that has_value()"""
        for coll in self.collections:
            for p in coll.valued():
                yield p

    def is_optional(self):
        return all(coll.is_optional() for coll in self.collections)

    def _update_from_spec(self, other):
        """Updates this spec by adding other items to it."""
        for coll in other.collections:
            self.append(coll)

        self.includes = list(set(self.includes+other.includes))
        self.dependencies = list(set(self.dependencies+other.dependencies))
        self.keys = list(set(self.keys+other.keys))
        self.evaluators = list(set(self.evaluators+other.evaluators))

    def _update_from_dict(self, other):
        """Updates parameters one at a time."""
        for k, v in other.items():
            self[k] = v
    
    def update(self, other):
        if isinstance(other, Spec):
            self._update_from_spec(other)
        else:
            self._update_from_dict(other)
                
    def copy(self):
        return Spec([coll.copy() for coll in self.collections],
                    includes=copy.copy(self.includes),
                    dependencies=copy.copy(self.dependencies),
                    keys=copy.copy(self.keys),
                    evaluators=copy.copy(self.evaluators)
                    )

                
    
class OneOf(Spec):
    """A collection of ParameterCollections, enabling branch selection.

    Enables ONE OF ... OR ... OR ... END constructs.
    """
    def __init__(self, *args):
        """Accepts a list of collections, each one a branch of the ONE OF logic."""
        self.branch_index = None
        super(OneOf, self).__init__(*args)

    def __setitem__(self, k, v):
        if type(k) is str:
            index = self._find_key(k)
            if self.branch_index is None:
                self.branch_index = index
            elif self.branch_index != index:
                raise RuntimeError(f'Attempting to set parameter "{k}" value in previously pruned branch.')
            self.collections[self.branch_index][k] = v
                
        else:
            super(OneOf, self).__setitem__(k,v)

    def __str__(self):
        if self.branch_index is None:
            return 'ONE OF:\n' + \
                '\nOR:\n'.join([ats_input_spec.colors.indent(str(coll)) for coll in self.collections])
        else:
            return str(self.collections[self.branch_index])
            
    def is_complete(self):
        # two ways to be complete -- either the collection index is
        # provided and that collection is complete, or the collection index
        # isn't provided but one of the collections is complete --
        # because all pars in that collection are optional!
        if self.branch_index is not None:
            return self.collections[self.branch_index].is_complete()
        else:
            return any(b.is_complete() for b in self.collections)

    def complete(self):
        """Generator for complete parameters."""
        if self.branch_index is not None:
            for p in self.collections[self.branch_index].complete():
                yield p
        
    def has_value(self):
        return self.branch_index is not None and \
            self.collections[self.branch_index].has_value()

    def valued(self):
        """Generator for parameters that has_value()"""
        if self.branch_index is not None:
            for p in self.collections[self.branch_index].valued():
                yield p

    def copy(self):
        return OneOf([coll.copy() for coll in self.collections])
                
            

class CaseSwitch:
    """A single parameter, whose value sets a series of other inclusions.

    Enables CASE ... SWITCH(a) ... SWITCH(b) ... SWITCH() ... END
    Enables IF ... THEN ... ELSE ... END
    """
    def __init__(self, case, switch_dict):
        assert(type(case) is Parameter)
        assert(case.is_primitive())
        self.case = case

        for k,v in switch_dict.items():
            assert(type(k) is case.ptype)
            assert(type(v) is ParameterCollection)
        self.branches = switch_dict

    def __getitem__(self, k):
        if k == self.case.name:
            return self.case.get()
        elif self.case.is_complete():
            return self.branches[self.case.get()][k]
        else:
            raise KeyError(f'Cannot access CaseSwitch branch until case "{self.case.name}" is set.')
        
    def __setitem__(self, k, v):
        if k == self.case.name:
            self.case.set(v)
        else:
            try:
                switch, branch = next((s,b) for (s, b) in self.branches.items() if k in b)
            except StopIteration:
                raise KeyError(f'Parameter "{k}" is not in the CaseSwitch.')
            else:
                if self.case.get() == switch:
                    branch[k] = v
                else:
                    raise KeyError(f'In a CaseSwitch, set the case "{self.case.name}" value prior to setting parameters in the branch.')
        
    def __contains__(self, k):
        return (k == self.case.name) or any(k in branch for branch in self.branches.values())

    def __str__(self):
        if self.case.is_complete():
            return self._str_branch_selected()
        elif self.case.ptype is bool:
            return self._str_ifthen()
        else:
            return self._str_caseswitch()

    def _str_branch_selected(self):
        return '%s\n%s'%(self.case,self.branches[self.case.get()])
        
    def _str_ifthen(self):
        lines = ['IF:',
                 ats_input_spec.colors.indent(str(self.case)),
                 'THEN:',
                 ats_input_spec.colors.indent(str(self.branches[True])),
                 'ELSE:',
                 ats_input_spec.colors.indent(str(self.branches[False])),
                 'END']
        return '\n'.join(lines)

    def _str_caseswitch(self):
        lines = ['CASE:',
                 ats_input_spec.colors.indent(str(self.case))]
        for key, switch in self.branches.items():
            lines.extend([ f'SWITCH({key}):',
                           ats_input_spec.colors.indent(str(switch)), ]),
        lines.append('END')
        return '\n'.join(lines)
    
    def is_complete(self):
        if not self.case.is_complete():
            return False
        return self.branches[self.case.get()].is_complete()

    def complete(self):
        """Generator for complete parameters."""
        if self.case.is_complete():
            yield self.case
            
            for p in self.branches[self.case.get()].complete():
                yield p
    
    def has_value(self):
        if self.case.has_value():
            return True
        elif self.case.is_complete():
            return self.branches[self.case.get()].has_value()
        else:
            return False

    def valued(self):
        """Generator for parameters that has_value()"""
        if self.case.has_value():
            yield self.case
        if self.case.is_complete():
            for p in self.branches[self.case.get()].valued():
                yield p

    def parameters(self):
        yield self.case
        for branch in self.branches.values():
            for p in branch.parameters():
                yield p

    def copy(self):
        case_copy = self.case.copy()
        switch_copy = dict([(k, v.copy()) for (k,v) in self.branches.items()])
        return CaseSwitch(case_copy, switch_copy)

                
                
class TypedCollection(ParameterCollection):
    """A ParameterCollection that stores things of a single type."""
    def __init__(self, contained_ptype):
        if type(contained_ptype) is str:
            self.contained_ptype_string = contained_ptype
            self.contained_ptype = None
        else:
            self.contained_ptype_string = 'TypedCollection'
            self.contained_ptype = contained_ptype

        self._primitive = self.contained_ptype in ats_input_spec.primitives.valid_types
        super(TypedCollection, self).__init__(list(),
                                              policy_not_in_spec='none',
                                              policy_empty_is_complete=False)
    def append_empty(self, k):
        """Add an empty Parameter of type contained_ptype and key k"""
        if k in self:
            raise ValueError(f'Key "{k}" already exists, cannot append_empty() of this name.')
        if self.contained_ptype is None:
            raise RuntimeError('Cannot append_empty() on TypedCollection whose type has not yet been set.')
        elif self._primitive:
            self._pars[k] = Parameter(k, self.contained_ptype)
            return self._pars[k]
        else:
            self._pars[k] = Parameter(k, self.contained_ptype_string, value=self.contained_ptype.copy())
            return self._pars[k].get()

    def __setitem__(self, k, v):
        if self.contained_ptype is None:
            raise RuntimeError('Cannot __setitem__() on TypedCollection whose type has not yet been set.')
        elif self._primitive:
            v = ats_input_spec.primitives.valid_from_type(self.contained_ptype, v)
            super(TypedCollection, self).__setitem__(k, v)
        else:
            raise NotImplementedError('It is unclear whether this should be implemented...')
            # append empty and copy in seems to be the best way to
            # ensure the same type structure?  will this work?  Will
            # this branch even ever be used?  How would v be
            # constructed in the first place?
            v1 = self.append_empty(k)
            for p1, p2 in zip(v1.parameters(), v2.parameters()):
                p1 = p2

    def copy(self):
        return TypedCollection(self.contained_ptype.copy())


class TypedSpec(Spec):
    def __init__(self, my_type, policy='standard', others=None, **kwargs):
        self.type = my_type
        self.policy = policy
        if policy not in ['standard', 'inline', 'sublist', 'sublistdash']:
            raise ValueError(f'Invalid policy "{self.policy}"')

        collections = []
        if others is not None:
            # check for the type par in others and remove it
            if self.type+' type' in others:
                others.pop(self.type+' type')
            if len(list(others.parameters())) > 0:
                collections.append(others)
        self.others = others
        
        if self.policy == 'standard' or self.policy == 'inline':
            type_par = Parameter(self.type+' type', ptype=str, **kwargs)
            # note the policy=none here allows this collection to be
            # extended when the type is set.
            par_coll = ParameterCollection([type_par,], policy_not_in_spec='none')
            collections.insert(0, par_coll)
            super(TypedSpec, self).__init__(collections)
        else:
            # create an empty list
            if len(collections) > 0:
                super(TypedSpec, self).__init__(collections)
            else:
                super(TypedSpec, self).__init__()

    def set_type(self, typename, typed_spec):
        if self.policy == 'standard' or self.policy == 'inline':
            # set the type parameter, call the super one in case we decide to
            # implement __setitem__ here to call set_type()
            super(TypedSpec, self).__setitem__(self.type+' type', typename)
            
        if self.policy == 'standard':
            # the typed spec goes under "typename parameters" sublist
            plist_name = typename+' parameters'
            self[0][plist_name] = typed_spec
        elif self.policy == 'inline':
            # the typed spec goes in this list
            self.append(typed_spec)
        elif self.policy == 'sublist':
            sublist_name = self.type+": "+typename
            # the typed spec goes under a new list whose name is typename
            typed_sublist = Parameter(sublist_name, value=typed_spec)
            par_coll = ParameterCollection([typed_sublist,])
            self.append(par_coll)
        elif self.policy == 'sublistdash':
            sublist_name = (self.type+"-"+typename).replace(' ', DELIMITER)
            # the typed spec goes under a new list whose name is typename
            typed_sublist = Parameter(sublist_name, value=typed_spec)
            par_coll = ParameterCollection([typed_sublist,])
            self.append(par_coll)
        else:
            raise ValueError(f'Invalid policy "{self.policy}"')
        return self.get_sublist()

    def get_sublist(self):
        """Returns the parameters list associated with the type."""
        if self.policy == 'standard':
            typename = self[self.type+' type']
            plist_name = typename+' parameters'
            return self[plist_name]
        elif self.policy == 'inline':
            return self
        elif self.policy.startswith('sublist'):
            return next(self.parameters()).get()

    def has_value(self):
        if self.policy.startswith('sublist') and len(self) > 0:
            return True
        else:
            return super(TypedSpec, self).has_value()

    def copy(self):
        others = None
        if self.others is not None:
            others = self.others.copy()
        return TypedSpec(self.type, self.policy, others)
                

class SpecDict(collections.abc.MutableMapping):
    """A dictionary that returns by copy and fills sublists."""
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self['list'] = ParameterCollection(policy_not_in_spec='none')

    def __getitem__(self, key):
        # includes specs we can construct on the fly
        if key.endswith('-list'):
            contained = self[key[:-len('-list')]]
            tc = ats_input_spec.specs.TypedCollection(contained)
            #result = ats_input_spec.specs.Spec([tc,])
            return tc
        elif key.endswith('-typed-spec'):
            contained_name = key[:-len('-typed-spec')].replace(DELIMITER, ' ')
            if key in self._store:
                others = self._store[key].copy()
            else:
                others = None
            result = TypedSpec(contained_name, policy='standard', others=others)
        elif key.endswith('-typedinline-spec'):
            contained_name = key[:-len('-typedinline-spec')].replace(DELIMITER, ' ')
            if key in self._store:
                others = self._store[key].copy()
            else:
                others = None
            result = TypedSpec(contained_name, policy='inline', others=others)
        elif key.endswith('-typedsublist-spec'):
            contained_name = key[:-len('-typedsublist-spec')].replace(DELIMITER, ' ')
            if key in self._store:
                others = self._store[key].copy()
            else:
                others = None
            result = TypedSpec(contained_name, policy='sublist', others=others)
        elif key.endswith('-typedsublistdash-spec'):
            contained_name = key[:-len('-typedsublistdash-spec')].replace(DELIMITER, ' ')
            if key in self._store:
                others = self._store[key].copy()
            else:
                others = None
            result = TypedSpec(contained_name, policy='sublistdash', others=others)
        else:
            result = self._store[key].copy()

        # add in included specs, recursively
        if hasattr(result, 'includes'):
            while len(result.includes) > 0:
                for included_spec in copy.copy(result.includes):
                    result.update(self[included_spec[0]])
                    result.includes.remove(included_spec)

        # now fill the result
        populate_specs(result, self)
        return result
            
    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __delitem__(self, key):
        del self._store[key]    
                    
    def __setitem__(self, key, value):
        self._store[key] = value

    def update(self, other):
        assert(type(other) is SpecDict)
        self._store.update(other._store)


#
# A couple of default wrappers and helper functions
#
def populate_specs(container, known_specs):
    """Given a container of parameters, fill it with types."""
    for v in container.parameters():
        if not v.is_primitive() and v.get() is None:
            v.set(known_specs[v.ptype].copy())
            populate_specs(v.get(), known_specs)

def get_spec(name, iterable):
    """Mostly for testing, this just takes a bunch of pars and makes a spec."""
    parlist = ParameterCollection(iterable)
    # make a copy on return to not effect the inputs
    return Spec([parlist,]).copy()


