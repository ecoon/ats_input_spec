"""tests lists of typed objects"""

import pytest
import ats_input_spec.printing
import ats_input_spec.source_reader
import logging

# type is contained


lines1 = """
``[top-spec]``
* `"typed list`" ``[my-typed-spec-list]``

``[my-typed-spec]``
* `"my type`" ``[string]``

``[my-a-spec]``
* `"a parameter`" ``[string]``

``[my-b-spec]``
* `"b parameter`" ``[string]``

""".split('\n')

@pytest.fixture
def known1():
    known_specs = ats_input_spec.source_reader.load_specs_from_lines("a_file", lines1)
    assert(len(known_specs) == 5)
    yield known_specs
    
def test_typed_one1(known1):
    outer = known1['my-typed-spec-list']
    print(outer)
    assert(not outer.is_complete())
    a = outer.append_empty('my a thing')
    a.set_type('a', known1['my-a-spec'])
    assert(not outer.is_complete())

    outer['my a thing']['a parameters']['a parameter'] = 'yay'
    print('my outer', outer)
    assert(outer.is_complete())
    print("===============")

    
def test_typed_two(known1):
    outer = known1['my-typed-spec-list']
    print('my outer', outer)
    print("---")
    assert(not outer.is_complete())

    # add a new one and set the type to a, which populates it with a's parameters
    a = outer.append_empty('my a thing')
    a.set_type('a', known1['my-a-spec'])
    print(outer)
    print("---")
    assert(not outer.is_complete())

    # set a's parameters
    outer['my a thing']['a parameters']['a parameter'] = 'yay'
    print(outer)
    print("---")
    assert(outer.is_complete())
    assert(outer['my a thing']['my type'] == 'a')

    # append a new one and set the type to b
    outer.append_empty('my b thing')
    # alternate way of setting
    outer['my b thing'].set_type('b', known1['my-b-spec'])
    print(outer)
    print("---")
    assert(outer['my b thing']['my type'] == 'b')
    assert(not outer.is_complete())

    with pytest.raises(KeyError):
        outer['my b']['b parameters']['a parameter'] = 'hi'
    outer['my b thing']['b parameters']['b parameter'] = 'bye'
    print('my outer', outer)
    assert(outer.is_complete())
    print("===============")
    

# type is inline
lines2 = """
``[top-spec]``
* `"typedinline list`" ``[my-typedinline-spec-list]``

``[my-typedinline-spec]``
* `"my type`" ``[string]``

``[my-a-spec]``
* `"a parameter`" ``[string]``

``[my-b-spec]``
* `"b parameter`" ``[string]``
""".split('\n')
@pytest.fixture
def known2():
    known_specs = ats_input_spec.source_reader.load_specs_from_lines("a_file", lines2)
    assert(len(known_specs) == 5)
    yield known_specs
    
def test_inline_typed_one(known2):
    # create an empty outer list
    outer = known2['my-typedinline-spec-list']
    print('my outer', outer)
    print("---")
    assert(not outer.is_complete())

    # add an empty and set type to a
    a = outer.append_empty('my a thing')
    a.set_type('my', known2['my-a-spec'])
    print('my outer', outer)
    print("---")
    assert(not outer.is_complete())

    # set the parameter in a
    outer['my a thing']['a parameter'] = 'yay'
    print('my outer', outer)
    assert(outer.is_complete())
    print("===============")


def test_inline_typed_two(known2):
    # create an empty outer list
    outer = known2['my-typedinline-spec-list']
    print('my outer', outer)
    print("---")
    assert(not outer.is_complete())

    # add an empty a
    outer.append_empty('my a')
    outer['my a'].set_type('my',known2['my-a-spec'])
    print('my outer', outer)
    print("---")
    assert(not outer.is_complete())

    # fill a
    outer['my a']['a parameter'] = 'yay'
    print('my outer', outer)
    print("---")
    assert(outer.is_complete())

    # add an empty b
    outer.append_empty('my b')
    outer['my b'].set_type('b', known2['my-b-spec'])
    print('my outer', outer)
    print("---")
    assert(not outer.is_complete())

    # fill b
    outer['my b']['b parameter'] = 'bye'
    print('my outer', outer)
    assert(outer.is_complete())
    print("===============")


# type is list
lines3 = """
``[top-spec]``
* `"typed sublist list`" ``[my-typedsublist-spec-list]``

``[my-typedsublist-spec]``

``[my-a-spec]``
* `"a parameter`" ``[string]``

``[my-b-spec]``
* `"b parameter`" ``[string]``
""".split('\n')

@pytest.fixture
def known3():
    known_specs = ats_input_spec.source_reader.load_specs_from_lines("a_file", lines3)
    yield known_specs
    
def test_typed_one3(known3):
    outer = known3['my-typedsublist-spec-list']
    print('my outer', outer)
    assert(not outer.is_complete())
    outer.append_empty('my a')
    outer['my a'].set_type('a', known3['my-a-spec'])
    assert(not outer.is_complete())

    outer['my a']['my: a']['a parameter'] = 'yay'
    assert(outer.is_complete())
    print('my outer', outer)


def test_typed_two3(known3):
    outer = known3['my-typedsublist-spec-list']
    assert(not outer.is_complete())
    outer.append_empty('my a')
    outer['my a'].set_type('a', known3['my-a-spec'])
    assert(not outer.is_complete())

    outer['my a']['my: a']['a parameter'] = 'yay'
    assert(outer.is_complete())

    outer.append_empty('my b')
    outer['my b'].set_type('b', known3['my-b-spec'])
    assert(not outer.is_complete())

    outer['my b']['my: b']['b parameter'] = 'bye'
    assert(outer.is_complete())

    print('my outer', outer)
