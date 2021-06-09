"""ats_input_spec/tests/test_printing.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Pretty printing tests.
"""
import ats_input_spec.printing
import ats_input_spec.specs

# def test_tostring():
#     list_of_ints = ats_input_spec.specs.get_typed_list("int-list", int)
#     my_list = list_of_ints()
    
#     print(ats_input_spec.printing.to_string("my list", my_list))

#     my_list = []
#     my_list.append(ats_input_spec.specs.PrimitiveParameter("one", float, 1.0))
#     my_list.append(ats_input_spec.specs.PrimitiveParameter("two", int))
#     my_list.append(ats_input_spec.specs.PrimitiveParameter("three", bool, optional=True))
#     my_class = ats_input_spec.specs.get_spec("my-spec", my_list)
#     my_obj = my_class()
#     print(ats_input_spec.printing.to_string("my spec", my_obj))


#     my_obj["two"] = 2
#     print(ats_input_spec.printing.to_string("my spec", my_obj))
#     #assert(False)

def test_help():
    my_list = []
    my_list.append(ats_input_spec.specs.PrimitiveParameter("one", float, 1.0))
    my_list.append(ats_input_spec.specs.PrimitiveParameter("two", int))
    my_list.append(ats_input_spec.specs.PrimitiveParameter("three", bool, optional=True))
    my_class = ats_input_spec.specs.get_spec("my-spec", my_list)
    my_obj = my_class()
    print(ats_input_spec.printing.help("my spec", my_obj))
    print("-------")
    my_obj["two"] = 2
    my_obj["one"] = 1.1
    print(ats_input_spec.printing.help("my spec", my_obj))
    #assert(False)

    
def test_help2():
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
    my_outer.append(ats_input_spec.specs.DerivedParameter("letters", my_leaf2_class, True))
    my_outer.append(ats_input_spec.specs.PrimitiveParameter("control", int))
    my_spec = ats_input_spec.specs.get_spec("my-outer",my_outer)
    assert(len(my_spec.spec) == 3)

    my_instance = my_spec()
    print(ats_input_spec.printing.help("my spec", my_instance))
    print("-------")
    my_instance["numbers"]["two"] = 2
    my_instance.fill_default("letters")
    my_instance["letters"]["b"] = 2
    print(ats_input_spec.printing.help("my spec", my_instance))
    #assert(False)
    

def test_help3():
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

    print(ats_input_spec.printing.help("my leaf", my_leaf_obj))

    my_leaf_obj["letter_or_number"] = 1
    print("---")
    print(ats_input_spec.printing.help("my leaf", my_leaf_obj))

    my_leaf_obj["a"] = 1
    print("---")
    print(ats_input_spec.printing.help("my leaf", my_leaf_obj))
    
    # print("---")
    # print(ats_input_spec.printing.help("my leaf spec", my_leaf_obj.__class__))

    #assert(False)
    
