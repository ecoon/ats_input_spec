"""ats_input_spec/test_specs.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)


Tests specs functionality
"""

import pytest

import ats_input_spec.specs as specs
import ats_input_spec.printing



def test_primitives():
    """Tests basic functionality of primitives."""
    p1 = specs.Parameter('mypar', float)
    assert(not p1.is_optional())
    assert(not p1.is_complete())
    assert(not p1.has_value())
    p1.set(3)
    assert(p1.is_complete())
    assert(p1.has_value())
    assert(p1.get() == 3.0)

    p2 = specs.Parameter('mypar', float, default=3.0)
    assert(p2.is_optional())
    assert(p2.is_complete())
    assert(not p2.has_value())
    assert(p2.get() == 3.0)
    p2.set(4.0)
    assert(p2.is_complete())
    assert(p2.has_value())
    assert(p2.get() == 4.0)

    p2 = specs.Parameter('mypar', float, default=3.0)
    assert(p2.is_optional())
    assert(p2.is_complete())
    assert(not p2.has_value())
    assert(p2.get() == 3.0)
    p2.set(4.0)
    assert(p2.is_complete())
    assert(p2.has_value())
    assert(p2.get() == 4.0)
    
def test_parlist():
    pars = {'mydouble' : specs.Parameter('mydouble', float),
            'myint' : specs.Parameter('myint', int)}
    pars = specs.ParameterCollection(pars)

    assert(not pars.is_complete())
    assert(not pars.has_value())
    assert(len(list(pars.complete())) == 0)
    assert(len(list(pars.valued())) == 0)

    pars['mydouble'] = 3.0
    assert(not pars.is_complete())
    assert(pars.has_value())
    assert(len(list(pars.complete())) == 1)
    assert(len(list(pars.valued())) == 1)

    pars['myint'] = 6
    assert(pars.is_complete())
    assert(pars.has_value())
    assert(len(list(pars.complete())) == 2)
    assert(len(list(pars.valued())) == 2)

    assert(pars['mydouble'] == 3.0)
    assert(pars['myint'] == 6)

def test_parlist_with_optional():
    pars = {'mydouble' : specs.Parameter('mydouble', float),
            'myint' : specs.Parameter('myint', int, default=6)}
    pars = specs.ParameterCollection(pars)

    assert(not pars.is_complete())
    assert(not pars.has_value())
    assert(len(list(pars.complete())) == 1)
    assert(len(list(pars.valued())) == 0)

    pars['mydouble'] = 3.0
    assert(pars.is_complete())
    assert(pars.has_value())
    assert(len(list(pars.complete())) == 2)
    assert(len(list(pars.valued())) == 1)

    assert(pars['mydouble'] == 3.0)
    assert(pars['myint'] == 6)
    
    pars['myint'] = 7
    assert(pars.is_complete())
    assert(pars.has_value())
    assert(len(list(pars.complete())) == 2)
    assert(len(list(pars.valued())) == 2)

    assert(pars['mydouble'] == 3.0)
    assert(pars['myint'] == 7)


def test_derived():
    xy = {'x' : specs.Parameter('x', float),
          'y' : specs.Parameter('y', float)}
    xy = specs.ParameterCollection(xy, 'xy-spec')
    p1 = specs.Parameter('xy', 'xy-spec')
    p1.set(xy)

    assert(not p1.is_optional())
    assert(not p1.is_complete())
    assert(not p1.has_value())
    p1.get()['x'] = 1.1
    p1.get()['y'] = 2.1
    assert(p1.is_complete())
    assert(p1.has_value())


def test_copy_primitive():
    p1 = specs.Parameter('mypar', float)
    p2 = p1.copy()
    p2.set(1.1)
    assert(p2.is_complete())
    assert(p2.is_primitive())
    assert(p2.has_value())
    assert(p2.get() == 1.1)
    assert(not p1.is_complete())
    assert(not p1.has_value())
    assert(p1.get() is None)


def test_copy_derived():
    xy = {'x' : specs.Parameter('x', float),
          'y' : specs.Parameter('y', float)}
    xy = specs.ParameterCollection(xy, 'xy-spec')
    p1 = specs.Parameter('xy', 'xy-spec')
    p1.set(xy)

    p2 = p1.copy()
    p2.get()['x'] = 1.1
    p2.get()['y'] = 2.1
    assert(p2.is_complete())
    assert(not p2.is_primitive())
    assert(p2.has_value())
    assert(p2.get()['x'] == 1.1)

    assert(not p1.is_complete())
    assert(not p1.is_primitive())
    assert(not p1.has_value())
    assert(p1.get()['x'] is None)
    
    
def test_usage_ParameterCollection():
    known_specs = dict()
    
    # first we read the file xy
    xy = {'x' : specs.Parameter('x', float),
          'y' : specs.Parameter('y', float)}
    xy = specs.ParameterCollection(xy)

    # register xy with the known_specs
    known_specs['xy-spec'] = xy
    
    # now we read the file main and register it
    main = {'my_xy' : specs.Parameter('my_xy', 'xy-spec'),
             'my_ab' : specs.Parameter('my_ab', 'ab-spec'),
             'my_other_xy' : specs.Parameter('my_other_xy', 'xy-spec'),
             'phi' : specs.Parameter('phi', float)}
    main = specs.ParameterCollection(main)
    known_specs['main-spec'] = main

    # finally read the file ab and register it
    ab = {'a' : specs.Parameter('a', str),
          'b' : specs.Parameter('b', int)}
    ab = specs.ParameterCollection(ab)
    known_specs['ab-spec'] = ab

    # now, create a main spec and populate it
    mymain = known_specs['main-spec'].copy()
    specs.populate_specs(mymain, known_specs)

    #  now fill it
    mymain['my_xy']['x'] = 1.1
    mymain['my_xy']['y'] = 2.1
    mymain['my_other_xy']['x'] = 3.1
    mymain['my_other_xy']['y'] = 4.1
    mymain['my_ab']['a'] = 'hello'
    mymain['my_ab']['b'] = 42
    mymain['phi'] = 6.1
    assert(mymain.is_complete())
    assert(mymain.has_value())

    # make sure also that we didn't populate the known_specs
    assert(known_specs['xy-spec']['x'] is None)
    assert(mymain['my_xy']['x'] == 1.1)
    assert(mymain['my_other_xy']['x'] == 3.1)    


def test_oneof1():
    x = specs.Parameter('x', float)
    y = specs.Parameter('y', float)
    z = specs.Parameter('z', float)

    branch1 = specs.ParameterCollection([x,])
    branch2 = specs.ParameterCollection([y,z])
    
    oneof = specs.OneOf([branch1, branch2])
    assert('x' in oneof)
    assert(len(oneof) == 2)
    assert(not oneof.is_complete())
    assert(not oneof.has_value())

    oneof['x'] = 1.1
    assert(oneof.is_complete())
    assert(oneof.has_value())
    with pytest.raises(RuntimeError):
        oneof['y'] = 2.1 # this errors because it is on the other branch

    assert(len(list(oneof.complete())) == 1)
    assert(len(list(oneof.valued())) == 1)
    assert(len(list(oneof.parameters())) == 3)
        
def test_oneof2():
    x = specs.Parameter('x', float)
    y = specs.Parameter('y', float)
    z = specs.Parameter('z', float, optional=True)

    branch1 = specs.ParameterCollection([x,])
    branch2 = specs.ParameterCollection([y,z])
    
    oneof = specs.OneOf([branch1, branch2])
    assert('y' in oneof)
    assert(len(oneof) == 2)
    assert(not oneof.is_complete())
    assert(not oneof.has_value())

    oneof['y'] = 1.1
    assert(oneof.is_complete())
    assert(oneof.has_value())
    with pytest.raises(RuntimeError):
        oneof['x'] = 2.1 # this errors because it is on the other branch
    assert(oneof.is_complete())
    assert(len(list(oneof.complete())) == 2)
    assert(len(list(oneof.valued())) == 1)
    assert(len(list(oneof.parameters())) == 3)
    oneof['z'] = 3.3
    assert(oneof.is_complete())
    assert(len(list(oneof.complete())) == 2)
    assert(len(list(oneof.valued())) == 2)
    assert(len(list(oneof.parameters())) == 3)

def test_caseswitch():
    case = specs.Parameter('case', str)
    x = specs.Parameter('x', float)
    y = specs.Parameter('y', float, optional=True)
    z = specs.Parameter('z', float, optional=True)
    branch1 = specs.ParameterCollection([x,])
    branch2 = specs.ParameterCollection([y,z])

    cs = specs.CaseSwitch(case, {'a':branch1, 'b':branch2})
    assert(not cs.is_complete())
    assert(not cs.has_value())
    assert(len(list(cs.parameters())) == 4)

    cs.case.set('a')
    assert(not cs.is_complete())
    assert(cs.has_value())
    assert(len(list(cs.complete())) == 1)
    assert(len(list(cs.valued())) == 1)

    cs['case'] = 'a'
    assert(not cs.is_complete())
    assert(cs.has_value())
    assert(len(list(cs.complete())) == 1)
    assert(len(list(cs.valued())) == 1)
    assert(cs.case.get() == 'a')
    assert(cs['case'] == 'a')

    cs['x'] = 1.1
    assert(cs.is_complete())
    assert(len(list(cs.complete())) == 2)
    assert(len(list(cs.valued())) == 2)
    assert(cs['x'] == 1.1)

    with pytest.raises(KeyError):
        cs['y'] = 2.2


def test_usage_oneof_caseswitch():
    """Tests a file that has a few pars, a OneOf, and a CaseSwitch."""
    known_specs = dict()
    
    # first we read the file xy
    xy = {'x' : specs.Parameter('x', float),
          'y' : specs.Parameter('y', float, optional=True)}
    xy = specs.ParameterCollection(xy)
    known_specs['xy-spec'] = xy
    
    # now we read the file main and register it
    # - main has some "other" parameters
    main_others = {'my_xy' : specs.Parameter('my_xy', 'xy-spec'),
            'phi' : specs.Parameter('phi', float)}
    main_others = specs.ParameterCollection(main_others)

    # - main has a oneof
    f = specs.Parameter('f', float)
    g = specs.Parameter('g', float, optional=True)
    branch1 = specs.ParameterCollection([f,g])
    my_ab = specs.Parameter('my_ab', 'ab-spec')
    branch2 = specs.ParameterCollection([my_ab,])
    main_oneof = specs.OneOf([branch1, branch2])

    # - main has a case-switch
    case = specs.Parameter('case', bool, default=True)
    jk = specs.Parameter('jk', 'xy-spec')
    mn = specs.Parameter('mn', 'ab-spec')
    main_caseswitch = specs.CaseSwitch(case,
                                       {True : specs.ParameterCollection([jk,]),
                                        False : specs.ParameterCollection([mn,])})

    known_specs['main-spec'] = \
        specs.Spec([main_others, main_oneof, main_caseswitch])
    
    # finally read the file ab and register it
    ab = {'a' : specs.Parameter('a', str),
          'b' : specs.Parameter('b', int)}
    ab = specs.ParameterCollection(ab)
    known_specs['ab-spec'] = ab
    
    # now, create a main spec and populate it
    mymain = known_specs['main-spec'].copy()
    specs.populate_specs(mymain, known_specs)

    #  now fill it
    assert(not mymain.is_complete())
    assert(not mymain.has_value())
    mymain['my_xy']['x'] = 1.1
    mymain['phi'] = 2.1
    mymain['f'] = 3.1
    mymain['case'] = False
    mymain['mn']['a'] = 'hello'
    assert(not mymain.is_complete())
    assert(mymain.has_value())
    mymain['mn']['b'] = 42
    assert(mymain.is_complete())
    

def test_typed_list_primitive():
    # make a list of floats
    tl = specs.TypedCollection(float)
    assert(len(tl) == 0)
    assert(not tl.is_complete())
    assert(not tl.has_value())

    # add one via append_empty
    x = tl.append_empty('x')
    x.set(1.1)
    assert(len(tl) == 1)
    assert(tl.is_complete())
    assert(tl.has_value())
    assert(tl['x'] == 1.1)

    # add one via set_item
    tl['y'] = 2.2
    assert(len(tl) == 2)
    assert(tl.is_complete())
    assert(tl.has_value())
    assert(tl['y'] == 2.2)
    assert(tl['x'] == 1.1)

    # add a string, throws!
    with pytest.raises(TypeError):
        tl['z'] = 'hello'
    
    assert(len(list(tl.complete())) == 2)
    assert(len(list(tl.valued())) == 2)


def test_typed_list_derived():
    # type to be stored
    xy = {'x' : specs.Parameter('x', float),
          'y' : specs.Parameter('y', float)}
    xy = specs.ParameterCollection(xy)

    # make a list of xy objects
    tl = specs.TypedCollection(xy)
    assert(len(tl) == 0)
    assert(not tl.is_complete())
    assert(not tl.has_value())

    # add one via append_empty
    min_c = tl.append_empty('lower coordinate')
    min_c['x'] = 1.1
    assert(len(tl) == 1)
    assert(not tl.is_complete())
    assert(tl.has_value())
    assert(tl['lower coordinate']['x'] == 1.1)
    tl['lower coordinate']['y'] = 2.1
    assert(len(tl) == 1)
    assert(tl.is_complete())
    assert(tl.has_value())
    assert(tl['lower coordinate']['x'] == 1.1)
    assert(tl['lower coordinate']['y'] == 2.1)

    # add another via append_empty
    max_c = tl.append_empty('upper coordinate')
    max_c['x'] = 3.1
    assert(len(tl) == 2)
    assert(not tl.is_complete())
    assert(tl.has_value())
    assert(tl['upper coordinate']['x'] == 3.1)
    assert(tl['lower coordinate']['x'] == 1.1)
    tl['upper coordinate']['y'] = 4.1
    assert(len(tl) == 2)
    assert(tl.is_complete())
    assert(tl.has_value())
    assert(tl['lower coordinate']['x'] == 1.1)
    assert(tl['lower coordinate']['y'] == 2.1)
    assert(tl['upper coordinate']['x'] == 3.1)
    assert(tl['upper coordinate']['y'] == 4.1)
    
    # add another of the same name
    with pytest.raises(ValueError):
        tl.append_empty('lower coordinate')
    
    assert(len(list(tl.complete())) == 2)
    assert(len(list(tl.valued())) == 2)
    

def test_typed_spec_standard():
    # parameters for type "ab"
    ab = {'a' : specs.Parameter('a', str),
          'b' : specs.Parameter('b', int)}
    ab = specs.ParameterCollection(ab)

    ts = specs.TypedSpec('wrm', policy='standard')
    assert(not ts.is_complete())
    assert(not ts.has_value())
    ts.set_type('ab', ab)
    assert(not ts.is_complete())
    assert(len(list(ts.complete())) == 1)
    assert(len(list(ts.parameters())) == 2)
    assert(ts.has_value())
    assert(ts['wrm type'] == 'ab')
    ts['ab parameters']['a'] = 'hello'
    ts['ab parameters']['b'] = 3
    assert(ts.is_complete())
    assert(len(list(ts.complete())) == 2)
    assert(len(list(ts.parameters())) == 2)
    assert(ts.has_value())
    assert(ts['ab parameters']['a'] == 'hello')


def test_typed_spec_inlined():
    # parameters for type "ab"
    ab = {'a' : specs.Parameter('a', str),
          'b' : specs.Parameter('b', int)}
    ab = specs.ParameterCollection(ab)

    ts = specs.TypedSpec('wrm', policy='inline')
    assert(not ts.is_complete())
    assert(not ts.has_value())
    ts.set_type('ab', ab)
    assert(not ts.is_complete())
    assert(len(list(ts.complete())) == 1)
    assert(len(list(ts.parameters())) == 3)
    assert(ts.has_value())
    assert(ts['wrm type'] == 'ab')
    ts['a'] = 'hello'
    ts['b'] = 3
    assert(ts.is_complete())
    assert(len(list(ts.complete())) == 3)
    assert(len(list(ts.parameters())) == 3)
    assert(ts.has_value())
    assert(ts['a'] == 'hello')


def test_typed_spec_sublist():
    # parameters for type "ab"
    ab = {'a' : specs.Parameter('a', str),
          'b' : specs.Parameter('b', int)}
    ab = specs.ParameterCollection(ab)

    ts = specs.TypedSpec('wrm', policy='sublist')
    assert(not ts.is_complete())
    assert(not ts.has_value())
    ts.set_type('ab', ab)
    assert(not ts.is_complete())
    assert(len(list(ts.complete())) == 0)
    assert(len(list(ts.parameters())) == 1)
    assert(ts.has_value())
    assert(next(ts.parameters()).name == 'wrm: ab')
    ts['wrm: ab']['a'] = 'hello'
    ts['wrm: ab']['b'] = 3
    assert(ts.is_complete())
    assert(len(list(ts.complete())) == 1)
    assert(len(list(ts.parameters())) == 1)
    assert(ts.has_value())
    assert(ts['wrm: ab']['a'] == 'hello')

def test_list_typed_spec():
    # parameters for type "ab"
    ab = {'a' : specs.Parameter('a', str),
          'b' : specs.Parameter('b', int, optional=True)}
    ab = specs.ParameterCollection(ab)
    
    # type to be stored
    xy = {'x' : specs.Parameter('x', float),
          'y' : specs.Parameter('y', float, optional=True)}
    xy = specs.ParameterCollection(xy)

    # list of typed
    ts = specs.TypedSpec('regions')
    tc = specs.TypedCollection(ts)
    first_list = tc.append_empty('first')
    first_list.set_type('ab', ab)
    first_list['ab parameters']['a'] = 'hello'

    second_list = tc.append_empty('second')
    second_list.set_type('xy', xy)
    second_list['xy parameters']['x'] = 1.1
    assert(tc.is_complete())
    assert(len(list(tc.parameters())) == 2)





    
    
    

    
