"""ats_input_spec/source_reader.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)


Tests source_reader functionality.
"""

import ats_input_spec.specs
import ats_input_spec.source_reader
import pytest
import logging
from unittest import mock
logging.basicConfig(level=logging.DEBUG)


# override the parameter_from_lines generator to just do strings for testing
def parameter_from_lines(lines):
    name = " ".join([l.strip() for l in lines])
    return ats_input_spec.specs.Parameter(name=name, ptype=str)
    
t = """ 

/*!
abc
*/
"""

def test_find_one_comment():
    tlist = t.split("\n")
    lines = ats_input_spec.source_reader.find_all_comments(tlist)
    assert(len(lines) == 3)
    assert(lines[1] == "abc")


t2 = """ 

/*!
abc
*/

things stuff and things

/*!
abc
*/

other things

"""

def test_find_two_comments():
    tlist = t2.split("\n")
    lines = ats_input_spec.source_reader.find_all_comments(tlist)
    assert(len(lines) == 6)
    assert(lines[4] == "abc")

t3 = """

* asdf
""".split("\n")

t4 = """

IF: 
""".split("\n")
def test_advance():
    assert(ats_input_spec.source_reader.advance(0, t3) == 2)
    assert(ats_input_spec.source_reader.advance(0, t4) == 2)

    i = 0
    i = ats_input_spec.source_reader.advance(i, t3)
    assert(i == 2)
    i += 1
    i = ats_input_spec.source_reader.advance(i, t3)
    assert(i == len(t3))

    t5 = t3+t4
    i = 0
    i = ats_input_spec.source_reader.advance(i, t5)
    assert(i == 2)
    i += 1
    i = ats_input_spec.source_reader.advance(i, t5)
    assert(i == 6)
    

t5 = """

* asdf

""".split("\n")

t6 = """

* asdf a
  multiline comm
* a second

""".split("\n")

@mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
def test_getnext_param():
    i = ats_input_spec.source_reader.advance(0, t5)
    i, p = ats_input_spec.source_reader.getnext_param(i, t5)
    assert(i == 3)
    assert(p.name == "* asdf")

    i = ats_input_spec.source_reader.advance(0, t6)
    i, p = ats_input_spec.source_reader.getnext_param(i, t6)
    assert(i == 4)
    assert(p.name == "* asdf a multiline comm")
    i = ats_input_spec.source_reader.advance(i, t6)
    i, p = ats_input_spec.source_reader.getnext_param(i, t6)
    assert(i == 5)
    assert(p.name == "* a second")
    
    with pytest.raises(AssertionError):
        i = ats_input_spec.source_reader.getnext_param(0, t4)

t7 = """

ONE OF:
* a 
OR
* b
END
""".split("\n")
@mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
def test_oneof():
    i = ats_input_spec.source_reader.advance(0, t7)
    assert(i == 2)
    i, opts = ats_input_spec.source_reader.getnext_oneof(i, t7)
    assert(len(opts) == 2)
    assert(len(list(opts[0].parameters())) == 1)
    assert(len(list(opts[1].parameters())) == 1)


t8 = """
ONE OF:
* a 
* c
OR
* b
OR
* e
* f
END
""".split("\n")
@mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
def test_oneof2():
    i = ats_input_spec.source_reader.advance(0, t8)
    assert(i == 1)
    i, opts = ats_input_spec.source_reader.getnext_oneof(i, t8)
    assert(len(opts) == 3)
    assert(len(list(opts[0].parameters())) == 2)
    assert(len(list(opts[1].parameters())) == 1)
    assert(len(list(opts[2].parameters())) == 2)

t9 = """
ONE OF:
OR
* b
OR
* e
* f
END
""".split("\n")
@mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
def test_oneof3():
    i = ats_input_spec.source_reader.advance(0, t9)
    with pytest.raises(RuntimeError):
        i, opts = ats_input_spec.source_reader.getnext_oneof(i, t9)

t10 = """
ONE OF:
* e
* f
END
""".split("\n")
@mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
def test_oneof4():
    i = ats_input_spec.source_reader.advance(0, t10)
    with pytest.raises(RuntimeError):
        i, opts = ats_input_spec.source_reader.getnext_oneof(i, t10)
        

# # can't do nested yet
# t11 = """
# ONE OF:
# * a 
# OR
# ONE OF:
# * c
# OR 
# * d
# END
# END
# """.split("\n")
# @mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
# def test_oneof5():
#     i = ats_input_spec.source_reader.advance(0, t11)
#     assert(i == 1)
#     i, opts = ats_input_spec.source_reader.getnext_oneof(i, t11)
#     print(opts)
#     assert(len(opts) == 2)
#     assert(len(opts[0]) == 1)
#     assert(len(opts[1]) == 1)
#     assert(len(opts[1][0][0]) == 1)
#     assert(len(opts[1][0][1]) == 1)
#     assert(len(opts[1][0][1][0]) == 3)


t12 = """


* asdf 
ONE OF:
* b
OR

* c

OR 
* d

END
* d

""".split("\n")
@mock.patch('test_02_source_reader.ats_input_spec.source_reader.parameter_from_lines', parameter_from_lines)
def test_read():
    i, name, objs, others = ats_input_spec.source_reader.read_this_scope(0, t12)
    assert(len(objs) == 2)
    assert(len(objs[0]) == 3)
    assert(len(objs[1]) == 2)


t13 = """
IF:
* `"a`" ``[bool]``

THEN:
* `"b`" ``[string]``

END
* `"d`" ``[string]``


""".split("\n")
def test_ifthen():
    i = ats_input_spec.source_reader.advance(0, t13)
    assert(i == 1)
    i, objs = ats_input_spec.source_reader.getnext_if(i, t13)
    assert(len(objs.branches) == 2)
    assert(len(objs.branches[True]) == 1)
    assert(len(objs.branches[False]) == 0)
    assert(i == 8)

t14 = """
IF
* `"a`" ``[bool]``

THEN
* `"b`" ``[string]``
* `"c`" ``[string]``

ELSE
* `"e`" ``[string]``

END
* `"d`" ``[string]``

""".split("\n")
def test_ifthen2():
    i = ats_input_spec.source_reader.advance(0, t14)
    assert(i == 1)
    i, objs = ats_input_spec.source_reader.getnext_if(i, t14)
    assert(len(objs.branches) == 2)
    assert(len(objs.branches[True]) == 2)
    assert(len(objs.branches[False]) == 1)
    assert(i == 12)
    

t15 = """
IF
* `"a`" ``[bool]``

ELSE
* `"e`" ``[string]``

END
* `"d`" ``[string]``

""".split("\n")
def test_ifthen3():
    i = ats_input_spec.source_reader.advance(0, t15)
    assert(i == 1)
    i, objs = ats_input_spec.source_reader.getnext_if(i, t15)
    assert(len(objs.branches) == 2)
    assert(len(objs.branches[True]) == 0)
    assert(len(objs.branches[False]) == 1)
    assert(i == 8)
    
    
