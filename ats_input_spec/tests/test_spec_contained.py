"""tests a list of typed objects"""

import pytest
import ats_input_spec.known_specs
import ats_input_spec.printing
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
    ats_input_spec.known_specs.known_specs.clear()
    ats_input_spec.known_specs.load_specs_from_lines("a_file", lines1)
    ats_input_spec.known_specs.finish_load()
    assert(len(ats_input_spec.known_specs.known_specs) == 4)
    logging.debug("Keys: ", list(ats_input_spec.known_specs.known_specs.keys()))
    yield None
    ats_input_spec.known_specs.known_specs.clear()
    
def test_typed_one1(known1):
    outer = ats_input_spec.known_specs.known_specs['my-typed-spec-list']()
    ats_input_spec.printing.help('my outer', outer)
    assert(not outer.is_filled())
    outer.append_empty('a')
    outer['a']['my type'] = 'a'
    assert(not outer.is_filled())

    outer['a']['a parameters']['a parameter'] = 'yay'
    ats_input_spec.printing.help('my outer', outer)
    assert(outer.is_filled())
    print("===============")

    
def test_typed_two(known1):
    outer = ats_input_spec.known_specs.known_specs['my-typed-spec-list']()
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # add a new one and set the type to a, which populates it with a's parameters
    outer.append_empty('my a')
    outer['my a'].set_type('my', 'a')
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # set a's parameters
    outer['my a']['a parameters']['a parameter'] = 'yay'
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(outer.is_filled())
    assert(outer['my a']['my type'] == 'a')

    # append a new one and set the type to b
    outer.append_empty('my b')
    # alternate way of setting
    outer['my b']['my type'] = 'b'
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(outer['my b']['my type'] == 'b')
    assert(not outer.is_filled())

    with pytest.raises(KeyError):
        outer['my b']['b parameters']['a parameter'] = 'hi'
    outer['my b']['b parameters']['b parameter'] = 'bye'
    ats_input_spec.printing.help('my outer', outer)
    assert(outer.is_filled())
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
    ats_input_spec.known_specs.known_specs.clear()
    ats_input_spec.known_specs.load_specs_from_lines("a2_file", lines2)
    ats_input_spec.known_specs.finish_load()
    assert(len(ats_input_spec.known_specs.known_specs) == 4)
    logging.debug("Keys: ", list(ats_input_spec.known_specs.known_specs.keys()))
    yield None
    ats_input_spec.known_specs.known_specs.clear()
    
def test_inline_typed_one(known2):
    # create an empty outer list
    outer = ats_input_spec.known_specs.known_specs['my-typedinline-spec-list']()
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # add an empty and set type to a
    outer.append_empty('a')
    outer['a'].set_type('my', 'a')
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # set the parameter in a
    outer['a']['a parameter'] = 'yay'
    ats_input_spec.printing.help('my outer', outer)
    assert(outer.is_filled())
    print("===============")


def test_inline_typed_two(known2):
    # create an empty outer list
    outer = ats_input_spec.known_specs.known_specs['my-typedinline-spec-list']()
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # add an empty a
    outer.append_empty('my a')
    outer['my a'].set_type('my','a')
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # fill a
    outer['my a']['a parameter'] = 'yay'
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(outer.is_filled())

    # add an empty b
    outer.append_empty('my b')
    outer['my b']['my type'] = 'b'
    ats_input_spec.printing.help('my outer', outer)
    print("---")
    assert(not outer.is_filled())

    # fill b
    outer['my b']['b parameter'] = 'bye'
    ats_input_spec.printing.help('my outer', outer)
    assert(outer.is_filled())
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
    ats_input_spec.known_specs.load_specs_from_lines("a3_file", lines3)
    ats_input_spec.known_specs.finish_load()
    print("Keys: ", list(ats_input_spec.known_specs.known_specs.keys()))
    yield None
    ats_input_spec.known_specs.known_specs.clear()
    
def test_typed_one3(known3):
    outer = ats_input_spec.known_specs.known_specs['my-typedsublist-spec-list']()
    ats_input_spec.printing.help('my outer', outer)
    assert(not outer.is_filled())
    outer.append_empty('my a')
    outer['my a'].set_type('my', 'a')
    assert(not outer.is_filled())

    outer['my a']['my: a']['a parameter'] = 'yay'
    assert(outer.is_filled())
    ats_input_spec.printing.help('my outer', outer)


def test_typed_two3(known3):
    outer = ats_input_spec.known_specs.known_specs['my-typedsublist-spec-list']()
    assert(not outer.is_filled())
    outer.append_empty('my a')
    outer['my a'].set_type('my', 'a')
    assert(not outer.is_filled())

    outer['my a']['my: a']['a parameter'] = 'yay'
    assert(outer.is_filled())

    outer.append_empty('my b')
    outer['my b']['my type'] = 'b'
    assert(not outer.is_filled())

    outer['my b']['my: b']['b parameter'] = 'bye'
    assert(outer.is_filled())

    ats_input_spec.printing.help('my outer', outer)
