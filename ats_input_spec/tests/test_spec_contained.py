"""tests a list of typed objects"""

import pytest
import rethink.known_specs
import rethink.printing


# type is contained


lines1 = """
``[top-spec]``
* `"typed list`" ``[my-typed-spec-list]``

``[my-typed-spec]``
* `"my type`" ``[string]``

``[my-type-a-spec]``
* `"a parameter`" ``[string]``

``[my-type-b-spec]``
* `"b parameter`" ``[string]``
""".split('\n')

@pytest.fixture
def known1():
    rethink.known_specs.load_specs_from_lines("a_file", lines1)
    rethink.known_specs.finish_load()
    print("Keys: ", list(rethink.known_specs.known_specs.keys()))
    yield None
    rethink.known_specs.known_specs.clear()
    
def test_typed_one(known1):
    outer = rethink.known_specs.known_specs['my-typed-spec-list']()
    rethink.printing.help('my outer', outer)
    assert(not outer.is_filled())
    outer.append_empty('a')
    outer['a']['my type'] = 'a'
    assert(not outer.is_filled())

    outer['a']['a parameters']['a parameter'] = 'yay'
    assert(outer.is_filled())
    rethink.printing.help('my outer', outer)



def test_typed_two(known1):
    outer = rethink.known_specs.known_specs['my-typed-spec-list']()
    assert(not outer.is_filled())
    outer.append_empty('my a')
    outer['my a']['my type'] = 'a'
    assert(not outer.is_filled())

    outer['my a']['a parameters']['a parameter'] = 'yay'
    assert(outer.is_filled())

    outer.append_empty('my b')
    outer['my b']['my type'] = 'b'
    assert(not outer.is_filled())

    with pytest.raises(KeyError):
        outer['my b']['b parameters']['a parameter'] = 'hi'
    outer['my b']['b parameters']['b parameter'] = 'bye'
    assert(outer.is_filled())

    rethink.printing.help('my outer', outer)
    

# type is inline


lines2 = """
``[top-spec]``
* `"typedinline list`" ``[my-typedinline-spec-list]``

``[my-typedinline-spec]``
* `"my type`" ``[string]``

``[my-type-a-spec]``
* `"a parameter`" ``[string]``

``[my-type-b-spec]``
* `"b parameter`" ``[string]``
""".split('\n')

@pytest.fixture
def known2():
    rethink.known_specs.load_specs_from_lines("a2_file", lines2)
    rethink.known_specs.finish_load()
    print("Keys: ", list(rethink.known_specs.known_specs.keys()))
    yield None
    rethink.known_specs.known_specs.clear()
    
def test_typed_one(known2):
    outer = rethink.known_specs.known_specs['my-typedinline-spec-list']()
    rethink.printing.help('my outer', outer)
    assert(not outer.is_filled())
    outer.append_empty('a')
    outer['a']['my type'] = 'a'
    assert(not outer.is_filled())

    outer['a']['a parameter'] = 'yay'
    assert(outer.is_filled())
    rethink.printing.help('my outer', outer)


def test_typed_two(known2):
    outer = rethink.known_specs.known_specs['my-typedinline-spec-list']()
    assert(not outer.is_filled())
    outer.append_empty('my a')
    outer['my a']['my type'] = 'a'
    assert(not outer.is_filled())

    outer['my a']['a parameter'] = 'yay'
    assert(outer.is_filled())

    outer.append_empty('my b')
    outer['my b']['my type'] = 'b'
    assert(not outer.is_filled())
    rethink.printing.help('my outer', outer)

    # with pytest.raises(KeyError):
    #     outer['my b']['a parameter'] = 'hi'
    outer['my b']['b parameter'] = 'bye'
    assert(outer.is_filled())

    rethink.printing.help('my outer', outer)

    
    assert(false)
    
