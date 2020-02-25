"""rethink/test_primitives.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)


Tests primitives functionality.
"""

import rethink.primitives as primitives
import pytest


def test_bool():
    assert(primitives.valid_from_type(bool, True))
    assert(primitives.valid_from_type(bool, False) is False)
    assert(primitives.valid_from_type(bool, 'True'))
    assert(primitives.valid_from_type(bool, 'False') is False)
    assert(primitives.valid_from_type(bool, 1))

    with pytest.raises(TypeError):
        primitives.valid_from_type(bool, 3.3)
        
    with pytest.raises(TypeError):
        primitives.valid_from_type(bool, '3.3')


def test_int():
    assert(primitives.valid_from_type(int, 123) is 123)
    assert(primitives.valid_from_type(int, '123') is 123)

    with pytest.raises(TypeError):
        primitives.valid_from_type(int, 3.3)
        
    with pytest.raises(TypeError):
        primitives.valid_from_type(int, '3.3')

def test_float():
    p = primitives.valid_from_type(float, 123)
    assert(type(p) is float)
    assert(p == 123.0)

    p = primitives.valid_from_type(float, 123.0)
    assert(type(p) is float)
    assert(p == 123.0)

    p = primitives.valid_from_type(float, '123.0')
    assert(type(p) is float)
    assert(p == 123.0)

    with pytest.raises(TypeError):
        primitives.valid_from_type(float, '3.3.')
        
    with pytest.raises(TypeError):
        primitives.valid_from_type(float, True)

def test_str():
    p = primitives.valid_from_type(str, 'abc')
    assert(type(p) is str)
    assert(p == 'abc')

    with pytest.raises(TypeError):
        primitives.valid_from_type(str, 3.3)

def test_list():
    p = primitives.valid_from_type(primitives.ListInt, [1,2,3])
    assert(type(p) is list)
    for ap in p:
        assert(type(ap) is int)
    assert(p == [1,2,3])


    with pytest.raises(TypeError):
        p = primitives.valid_from_type(primitives.ListInt, [1,2,3.0])

    with pytest.raises(TypeError):
        primitives.valid_from_type(primitives.ListInt, 'abc')

    with pytest.raises(TypeError):
        primitives.valid_from_type(primitives.ListStr, 'abc') # tricky!

        
def test_badtype():
    class Fail(object):
        pass
    with pytest.raises(TypeError):
        primitives.valid_from_type(Fail, 'abc')

