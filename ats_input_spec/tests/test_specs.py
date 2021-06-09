"""ats_input_spec/test_specs.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)


Tests specs functionality
"""

import pytest

import ats_input_spec.specs
import ats_input_spec.printing

def _tosizes(list_of_lists_of_lists):
    return [[len(alist) for alist in list_of_lists] for list_of_lists in list_of_lists_of_lists]

def _check(obj, filled, unfilled, optional=None, oneofs=None):
    if oneofs is None:
        is_filled = filled > 0 and unfilled == 0
    else:
        is_filled = unfilled + len(oneofs) == 0
    assert(is_filled == obj.is_filled())
    assert(len(list(obj.filled())) is filled)
    assert(len(list(obj.unfilled())) is unfilled)

    if optional is not None:
        assert(len(list(obj.optional())) is optional)
    else:
        with pytest.raises(AttributeError):
            obj.optional()

    if oneofs is not None:
        assert(_tosizes(obj.oneofs()) == oneofs)
    else:
        with pytest.raises(AttributeError):
            obj.oneofs()

def _checklen(obj, l):
    #    assert(len(obj) is l)
    pass

            
def test_list():
    glist = ats_input_spec.specs.GenericList()
    # empty list is full
    assert(glist.is_filled())


def test_typed_list_independence():
    list_of_doubles = ats_input_spec.specs.get_typed_list("double-list", float)
    list_of_ints = ats_input_spec.specs.get_typed_list("int-list", int)
    assert(list_of_doubles is not list_of_ints)
    assert(list_of_doubles.ContainedPType is float)
    assert(list_of_ints.ContainedPType is int)

def test_typed_list_append():
    list_of_ints = ats_input_spec.specs.get_typed_list("int-list", int)

    # empty list
    my_ints = list_of_ints()
    _check(my_ints, 0, 0)

    # one item, not assigned
    my_ints.append_empty('one')
    assert(my_ints['one'] is None)
    _check(my_ints, 0, 1)
    assert(my_ints['one'] is None)

    # assigned
    my_ints['one'] = 1
    _check(my_ints, 1, 0)
    assert(my_ints['one'] is 1)

    # another
    my_ints['two'] = 2
    assert(my_ints['one'] is 1)
    assert(my_ints['two'] is 2)
    _check(my_ints, 2, 0)


def test_leaf_spec():
    my_list = []
    my_list.append(ats_input_spec.specs.PrimitiveParameter("one", float, 1.0))
    my_list.append(ats_input_spec.specs.PrimitiveParameter("two", int))
    my_list.append(ats_input_spec.specs.PrimitiveParameter("three", bool, optional=True))

    my_class = ats_input_spec.specs.get_spec("my-spec", my_list)
    assert(len(my_class.spec) == 3)
    my_instance = my_class()
    _check(my_instance, 0, 1, 2, list())

    
    my_instance['one'] = 2.0
    _check(my_instance, 1, 1, 1, list())
    
    my_instance['two'] = 2
    _check(my_instance, 2, 0, 1, list())

    with pytest.raises(KeyError):
        my_instance["not here"] = 2
    _check(my_instance, 2, 0, 1, list())

def test_nonleaf():
    my_leaf = []
    my_leaf.append(ats_input_spec.specs.PrimitiveParameter("one", float, 1.0))
    my_leaf.append(ats_input_spec.specs.PrimitiveParameter("two", int))
    my_leaf.append(ats_input_spec.specs.PrimitiveParameter("three", bool, optional=True))
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    assert(len(my_leaf_class.spec) == 3)

    my_leaf2 = []
    my_leaf2.append(ats_input_spec.specs.PrimitiveParameter("a", str, 'abc'))
    my_leaf2.append(ats_input_spec.specs.PrimitiveParameter("b", int))
    my_leaf2.append(ats_input_spec.specs.PrimitiveParameter("c", str, optional=True))
    my_leaf2_class = ats_input_spec.specs.get_spec("my-spec2",my_leaf2)
    assert(len(my_leaf2_class.spec) == 3)
    
    my_outer = []
    my_outer.append(ats_input_spec.specs.DerivedParameter("numbers", my_leaf_class, False))
    my_outer.append(ats_input_spec.specs.DerivedParameter("letters", my_leaf2_class, False))
    my_outer.append(ats_input_spec.specs.PrimitiveParameter("control", int))
    my_spec = ats_input_spec.specs.get_spec("my-outer",my_outer)
    assert(len(my_spec.spec) == 3)
    
    my_instance = my_spec()
    _check(my_instance, 0, 3, 0, list())
    _check(my_instance, 0, 3, 0, list())

    my_instance["control"] = 2
    _check(my_instance, 1, 2, 0, list())

    my_num = my_instance["numbers"]
    _check(my_instance, 1, 2, 0, list())
    assert(type(my_num) is my_leaf_class)
    my_num["two"] = 2
    assert(my_num.is_filled())
    _check(my_instance, 2, 1, 0, list())

    my_instance["letters"]["b"] = 2
    _check(my_instance, 3, 0, 0, list())
    _checklen(my_instance,3)

def test_nonleaf_optional():
    my_leaf = []
    my_leaf.append(ats_input_spec.specs.PrimitiveParameter("one", float, 1.0))
    my_leaf.append(ats_input_spec.specs.PrimitiveParameter("three", bool, optional=True))
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    assert(len(my_leaf_class.spec) == 2)

    my_leaf2 = []
    my_leaf2.append(ats_input_spec.specs.PrimitiveParameter("b", int))
    my_leaf2_class = ats_input_spec.specs.get_spec("my-spec2",my_leaf2)
    assert(len(my_leaf2_class.spec) == 1)
    
    my_outer = []
    my_outer.append(ats_input_spec.specs.DerivedParameter("numbers", my_leaf_class, False))
    my_outer.append(ats_input_spec.specs.DerivedParameter("letters", my_leaf2_class, True))
    
    my_spec = ats_input_spec.specs.get_spec("my-outer", my_outer)
    my_instance = my_spec()
    _check(my_instance, 1, 0, 1, list())
    my_instance.fill_default("numbers") 
    _check(my_instance, 1, 0, 1, list())
    my_instance["numbers"]["one"] = 1.1
    _check(my_instance, 1, 0, 1, list())
    my_instance.fill_default("letters") 
    _check(my_instance, 1, 1, 0, list())
    my_instance["letters"]["b"] = 2
    _check(my_instance, 2, 0, 0, list())

def test_one_of1():
    """Simplest case -- one option in one 'oneof'"""
    my_leaf = []
    my_leaf.append(ats_input_spec.specs.PrimitiveParameter("one", float))
    my_leaf.append(ats_input_spec.specs.OneOfList())
    my_leaf[1].append([ats_input_spec.specs.PrimitiveParameter("a", int),])
    my_leaf[1].append([ats_input_spec.specs.PrimitiveParameter("b", int),])
                       
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _checklen(my_leaf_obj,1)
    _check(my_leaf_obj, 0, 2, 0, [[1,1]])

    my_leaf_obj["one"] = 1.0
    _checklen(my_leaf_obj,1)
    _check(my_leaf_obj, 1, 1, 0, [[1,1]])
    
    my_leaf_obj["a"] = 1
    _checklen(my_leaf_obj,2)
    _check(my_leaf_obj, 2, 0, 0, list())

    with pytest.raises(RuntimeError):
        my_leaf_obj["b"] = 3
    _checklen(my_leaf_obj,2)
    _check(my_leaf_obj, 2, 0, 0, list())
    
def test_one_of_with_optional():
    """Simplest case -- one option in one 'oneof'"""
    my_leaf = [ats_input_spec.specs.OneOfList(),]
    my_leaf[0].append(list())
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("b", int, True))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("one", int))
                       
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _checklen(my_leaf_obj,0)
    _check(my_leaf_obj, 0, 1, 0, [[2,1]])

    my_leaf_obj["a"] = 1
    _checklen(my_leaf_obj,1)
    _check(my_leaf_obj, 1, 0, 1, list())
    
    my_leaf_obj["b"] = 1
    _checklen(my_leaf_obj,2)
    _check(my_leaf_obj, 2, 0, 0, list())

    with pytest.raises(RuntimeError):
        my_leaf_obj["one"] = 3
    _checklen(my_leaf_obj,2)
    _check(my_leaf_obj, 2, 0, 0, list())
    

def test_one_of2():
    """Multiple options in a branch"""
    my_leaf = [ats_input_spec.specs.OneOfList(),]
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("b", int))

    my_leaf[0].append(list())
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("one", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("two", int))
    
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _checklen(my_leaf_obj,0)
    _check(my_leaf_obj, 0, 1, 0, [[2,2]])
    assert(my_leaf_obj.spec_oneof_inds[0] is None)

    my_leaf_obj["one"] = 1
    _checklen(my_leaf_obj,1)
    _check(my_leaf_obj, 1, 1, 0, list())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 1)
    my_leaf_obj["two"] = 2
    _check(my_leaf_obj, 2, 0, 0, list())
    _checklen(my_leaf_obj,2)

    with pytest.raises(RuntimeError):
        my_leaf_obj["a"] = 1

    _check(my_leaf_obj, 2, 0, 0, list())
    _checklen(my_leaf_obj,2)


def test_one_of3():
    """Three options"""
    my_leaf = [ats_input_spec.specs.OneOfList(),]
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("b", int))

    my_leaf[0].append(list())
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("one", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("two", int))

    my_leaf[0].append(list())
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("blue", int))
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("red", int))
    
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _check(my_leaf_obj, 0, 1, 0, [[2,2,2]])
    _checklen(my_leaf_obj,0)
    assert(my_leaf_obj.spec_oneof_inds[0] is None)

    my_leaf_obj["blue"] = 1
    _check(my_leaf_obj, 1, 1, 0, list())
    _checklen(my_leaf_obj,1)
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 2)

    with pytest.raises(RuntimeError):
        my_leaf_obj["a"] = 1
    with pytest.raises(RuntimeError):
        my_leaf_obj["one"] = 1

    my_leaf_obj["red"] = 2
    _check(my_leaf_obj, 2, 0, 0, list())

    

def test_shared_option():
    """Three options"""
    my_leaf = [ats_input_spec.specs.OneOfList(),]
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("b", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))

    my_leaf[0].append(list())
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("one", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("two", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))

    my_leaf[0].append(list())
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("blue", int))
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("red", int))
    
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _check(my_leaf_obj, 0, 1, 0, [[3,3,2]])
    _checklen(my_leaf_obj,0)
    assert(my_leaf_obj.spec_oneof_inds[0] is None)

    my_leaf_obj["letter_or_number"] = 1
    _check(my_leaf_obj, 1, 1, 0, [[2,2]])
    _checklen(my_leaf_obj,1)
    assert(not my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 2)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 0)
    assert(my_leaf_obj.spec_oneof_inds[0][1] is 1)

    with pytest.raises(RuntimeError):
        my_leaf_obj["blue"] = 1

    my_leaf_obj["a"] = 1
    _check(my_leaf_obj, 2, 1, 0, list())
    _checklen(my_leaf_obj,2)
    assert(not my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 0)

    with pytest.raises(RuntimeError):
        my_leaf_obj["blue"] = 1
    with pytest.raises(RuntimeError):
        my_leaf_obj["one"] = 1
    
    my_leaf_obj["b"] = 2
    _checklen(my_leaf_obj,3)
    assert(my_leaf_obj.is_filled())
    _check(my_leaf_obj, 3, 0, 0, list())


def test_shared_option2():
    """Three options"""
    my_leaf = [ats_input_spec.specs.OneOfList(),]
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("b", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))

    my_leaf[0].append(list())
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("one", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("two", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))

    my_leaf[0].append(list())
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("blue", int))
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("red", int))
    
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _check(my_leaf_obj, 0, 1, 0, [[3,3,2]])
    _checklen(my_leaf_obj,0)
    assert(not my_leaf_obj.is_filled())
    assert(my_leaf_obj.spec_oneof_inds[0] is None)

    my_leaf_obj["blue"] = 1
    _check(my_leaf_obj, 1, 1, 0, list())
    _checklen(my_leaf_obj,1)
    assert(not my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 2)

    with pytest.raises(RuntimeError):
        my_leaf_obj["letter_or_number"] = 1
    
    
    
def test_shared_option3():
    """Three options"""
    my_leaf = [ats_input_spec.specs.OneOfList(),]
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("b", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))

    my_leaf[0].append(list())
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("one", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("two", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("number_or_color", int))

    my_leaf[0].append(list())
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("blue", int))
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("red", int))
    my_leaf[0][2].append(ats_input_spec.specs.PrimitiveParameter("number_or_color", int))
    
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _check(my_leaf_obj, 0, 1, 0, [[3,4,3]])
    _checklen(my_leaf_obj,0)
    assert(not my_leaf_obj.is_filled())
    assert(my_leaf_obj.spec_oneof_inds[0] is None)

    my_leaf_obj["letter_or_number"] = 1
    _check(my_leaf_obj, 1, 1, 0, [[2,3]])
    _checklen(my_leaf_obj,1)
    assert(not my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 2)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 0)
    assert(my_leaf_obj.spec_oneof_inds[0][1] is 1)

    with pytest.raises(RuntimeError):
        my_leaf_obj["blue"] = 1
    
    my_leaf_obj["number_or_color"] = 1
    _check(my_leaf_obj, 2, 2, 0, list())
    _checklen(my_leaf_obj,2)
    assert(not my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 1)

    with pytest.raises(RuntimeError):
        my_leaf_obj["a"] = 1
    with pytest.raises(RuntimeError):
        my_leaf_obj["blue"] = 1

    my_leaf_obj["one"] = 1
    my_leaf_obj["two"] = 2
    _check(my_leaf_obj, 4, 0, 0, list())
    _checklen(my_leaf_obj,4)
    assert(my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 1)
        
    
    
def test_multiple():
    my_leaf = [ats_input_spec.specs.OneOfList(),ats_input_spec.specs.OneOfList()]
    my_leaf[0].append(list())
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("a", int))
    my_leaf[0][0].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))

    my_leaf[0].append(list())
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("red", int))
    my_leaf[0][1].append(ats_input_spec.specs.PrimitiveParameter("number_or_color", int))

    my_leaf[1].append(list())
    my_leaf[1][0].append(ats_input_spec.specs.PrimitiveParameter("one", int))
    my_leaf[1][0].append(ats_input_spec.specs.PrimitiveParameter("letter_or_number", int))
    my_leaf[1][0].append(ats_input_spec.specs.PrimitiveParameter("number_or_color", int))

    my_leaf[1].append(list())
    my_leaf[1][1].append(ats_input_spec.specs.PrimitiveParameter("cat", int))
    my_leaf[1][1].append(ats_input_spec.specs.PrimitiveParameter("dog", int))
    
    my_leaf_class = ats_input_spec.specs.get_spec("my-spec",my_leaf)
    my_leaf_obj = my_leaf_class()
    _check(my_leaf_obj, 0, 2, 0, [[2,2],[3,2]])
    _checklen(my_leaf_obj,0)
    assert(not my_leaf_obj.is_filled())
    assert(my_leaf_obj.spec_oneof_inds[0] is None)

    my_leaf_obj["letter_or_number"] = 1
    _check(my_leaf_obj, 1, 3, 0, list())
    _checklen(my_leaf_obj,1)
    assert(not my_leaf_obj.is_filled())
    assert(len(my_leaf_obj.spec_oneof_inds[0]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[0][0] is 0)
    assert(len(my_leaf_obj.spec_oneof_inds[1]) is 1)
    assert(my_leaf_obj.spec_oneof_inds[1][0] is 0)

    with pytest.raises(RuntimeError):
        my_leaf_obj["red"] = 1
    with pytest.raises(RuntimeError):
        my_leaf_obj["cat"] = 1
    
    my_leaf_obj["one"] = 1
    my_leaf_obj["a"] = 1
    _check(my_leaf_obj, 3, 1, 0, list())
    _checklen(my_leaf_obj,3)
    assert(not my_leaf_obj.is_filled())

    # this example shows the fragility of the current oneof system.
    # We cannot fill this spec, because we cannot simultaneously have
    # letter_or_number and number_or_color since they are conflicting
    # options to the 0th one-of, but we need both for the 1st one-of.
    with pytest.raises(RuntimeError):
        my_leaf_obj["number_or_color"] = 1
        _check(my_leaf_obj, 4, 0, 0, list())




    
