"""ats_input_spec/source_reader.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)


Tests source_reader functionality of the parameter_from_lines
function.

"""

import ats_input_spec.source_reader
import pytest

# test the parameter construction
def test_good():
    ps = '* `"my parameter`" ``[double]`` **1.0** my parameter doc'
    p = ats_input_spec.source_reader.parameter_from_lines([ps,])
    assert(p.name == "my parameter")
    assert(p.ptype is float)
    assert(p.default == 1.0)
    #assert(p.doc == "my parameter doc")

def test_good_no_default():
    ps = '* `"my parameter`" ``[double]`` my parameter doc'
    p = ats_input_spec.source_reader.parameter_from_lines([ps,])
    assert(p.name == "my parameter")
    assert(p.ptype is float)
    assert(p.default is None)
    #assert(p.doc == "my parameter doc")

def test_good_no_doc():
    ps = '* `"my parameter`" ``[double]`` '
    p = ats_input_spec.source_reader.parameter_from_lines([ps,])
    assert(p.name == "my parameter")
    assert(p.ptype is float)
    assert(p.default is None)
    #assert(p.doc == "")

def test_good_multiline():
    ps = ['* `"my parameter`" ``[double]`` **1.0** this has a','          multiline docstring']
    p = ats_input_spec.source_reader.parameter_from_lines(ps)
    assert(p.name == "my parameter")
    assert(p.ptype is float)
    assert(p.default == 1.0)
    #assert(p.doc == "this has a multiline docstring")


def test_good_plist_spec():
    ps = ['* `"my parameter list`" ``[my-spec]`` my spec is cool']
    p = ats_input_spec.source_reader.parameter_from_lines(ps)
    assert(p.name == "my parameter list")
    assert(p.ptype == 'my-spec')
    #assert(p.doc == "my spec is cool")
    
def test_good_with_spaces():
    ps = '  *       `"my parameter`"        ``[double]``     ** 1.0   **    my parameter doc    '
    p = ats_input_spec.source_reader.parameter_from_lines([ps,])
    assert(p.name == "my parameter")
    assert(p.ptype is float)
    assert(p.default == 1.0)
    #assert(p.doc == "my parameter doc")

def test_bad_name():
    ps = '  *  my parameter ``[double]`` **1.0** my parameter doc'
    with pytest.raises(RuntimeError):
        p = ats_input_spec.source_reader.parameter_from_lines([ps,])

def test_bad_type():
    ps = '  *  `"my parameter`" ``no-bracket`` **1.0** my parameter doc'
    with pytest.raises(RuntimeError):
        p = ats_input_spec.source_reader.parameter_from_lines([ps,])

def test_bad_default():
    ps = '  *  `"my parameter`" ``[float]`` **abc** my parameter doc'
    with pytest.raises(RuntimeError):
        p = ats_input_spec.source_reader.parameter_from_lines([ps,])

spec_text = """
* `"y0`" ``[double]`` y_0 in f = y0 + g * (x - x0)
* `"gradient`" ``[Array(double)]`` g in f = y0 + g * (x - x0)
* `"x0`" ``[Array(double)]`` x0 in f = y0 + g * (x - x0)
""".split('\n')
def test_read_multiple():
    assert(len(spec_text) == 5)
    print("My length in test:", len(spec_text))
    i, name, objects, others = ats_input_spec.source_reader.read_this_scope(0,spec_text)
    assert(len(objects) == 1)
    assert(len(list(objects[0].parameters())) == 3)


spec_text2 = """
``[my-first-spec]``
* `"y0`" ``[double]`` y_0 in f = y0 + g * (x - x0)
* `"gradient`" ``[Array(double)]`` g in f = y0 + g * (x - x0)
* `"x0`" ``[Array(double)]`` x0 in f = y0 + g * (x - x0)
``[my-second-spec]``
* `"y0`" ``[double]`` y_0 in f = y0 + g * (x - x0)
* `"gradient`" ``[Array(double)]`` g in f = y0 + g * (x - x0)
* `"x0`" ``[Array(double)]`` x0 in f = y0 + g * (x - x0)
""".split('\n')
def test_read_multiple_specs():
    specs = []
    i = 0
    while i < len(spec_text2):
        i, specname, objects, others = ats_input_spec.source_reader.read_this_scope(i,spec_text2)
        if specname is None:
            filebase = os.path.split(filename)[-1][:-3]
            specname = to_specname(filebase)
        specs.append((specname, objects))

    assert(len(specs) == 2)
    assert(specs[0][0] == "my-first-spec")
    assert(specs[1][0] == "my-second-spec")


spec_text3 = """
.. _my-new-style-spec:
.. admonition:: my-new-style-spec

    * `"y0`" ``[double]`` y_0 in f = y0 + g * (x - x0)
    * `"gradient`" ``[Array(double)]`` g in f = y0 + g * (x - x0)
    * `"x0`" ``[Array(double)]`` x0 in f = y0 + g * (x - x0)
""".split('\n')
def test_new_style_specs():
    specs = list()
    i = 0
    while i < len(spec_text3):
        i, specname, objects, others = ats_input_spec.source_reader.read_this_scope(i,spec_text3)
        specs.append((specname, objects))
    assert(len(specs) == 1)
    assert(len(objects) == 1)
    assert(len(list(objects[0].parameters())) == 3)


spec_text4 = """
this

``[an-empty-spec]``

is empty
""".split('\n')
def test_empty_spec():
    specs = []
    i = 0
    while i < len(spec_text4):
        i, specname, objects, others = ats_input_spec.source_reader.read_this_scope(i, spec_text4)
        specs.append((specname, objects))

    assert(len(specs) == 1)
    assert(specs[0][0] == "an-empty-spec")
    assert(len(objects) == 1)
    assert(len(list(objects[0].parameters())) == 0)
    
    
def test_to_specname():
    assert(ats_input_spec.source_reader.to_specname("BasicTest") == "basic-test-spec")
    assert(ats_input_spec.source_reader.to_specname("SecondTest2") == "second-test2-spec")
    assert(ats_input_spec.source_reader.to_specname("SecondTestC") == "second-test-c-spec")
    assert(ats_input_spec.source_reader.to_specname("WRMTest") == "wrm-test-spec")
    assert(ats_input_spec.source_reader.to_specname("EmbeddedWRMTest") == "embedded-wrm-test-spec")
    assert(ats_input_spec.source_reader.to_specname("FinalWRM") == "final-wrm-spec")
    assert(ats_input_spec.source_reader.to_specname("With_Underscore") == "with-underscore-spec")
    assert(ats_input_spec.source_reader.to_specname("BDF_FnBase") == "bdf-fn-base-spec")
    assert(ats_input_spec.source_reader.to_specname("wrm_van_genuchten") == "wrm-van-genuchten-spec")


spec_text_cv = """    
list is indexed by Region, and the regions (logically) should partition the
domain (or boundary of the domain in the case of BCs).

Each entry in that list is a:

``[composite-vector-function-spec]``

ONE OF:
* `"region`" ``[string]`` Region on which this function is evaluated.
OR:
* `"regions`" ``[Array(string)]`` List of regions on which this function is evaluated.
END

ONE OF:
* `"component`" ``[string]`` Mesh component to evaluate this on.  This is one of "cell", "face", "node", "edge",
  or "boundary_face". The last two may require additional conditions, such as a proper mesh initialization.
  The mask "*" could be used in place of the component name.
OR:
* `"components`" ``[Array(string)]`` Mesh components to evaluate this on.  This is some collection of "cell", "face", 
  "node", "edge", and/or "boundary_face". The last two may require additional conditions, such as a proper mesh 
  initialization.  The array with the single entry "*" could be used to initialize all existing components.
END

* `"function`" ``[function-spec]`` The spec to provide the actual algebraic function.  

""".split('\n')
def test_oneof_in_cv():
    specs = []
    i = 0
    while i < len(spec_text_cv):
        i, specname, objects, others = ats_input_spec.source_reader.read_this_scope(i, spec_text_cv)
        specs.append((specname, objects))

    assert(len(specs) == 1)
    assert(specname == 'composite-vector-function-spec')
    assert(len(objects) == 3) # two one-ofs and a parameter
    assert(len(objects[0].collections) == 2) # two branches in the oneof for region
    assert(next(objects[0].collections[0].parameters()).name == 'region')
    assert(len(objects[1].collections) == 2) # two branches in the oneof for component
    assert(next(objects[1].collections[0].parameters()).name == 'component')
    assert(len(objects[2]) == 1) # one parameter in the parlist

