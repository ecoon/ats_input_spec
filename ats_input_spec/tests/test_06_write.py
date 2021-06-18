"""ats_input_spec/public.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Tests for the public interface, full capability.

"""
import pytest
import ats_input_spec.public
import ats_input_spec.printing
import ats_input_spec.io

@pytest.fixture
def main():
    main = ats_input_spec.public.get_main()

    # add a mesh
    mesh_args = {"file":"../mymesh.exo"}
    ats_input_spec.public.add_domain(main, "domain", 3, "read mesh file", mesh_args)

    # end after one year, require daily syncronization
    main["cycle driver"]["end time"] = 1.0
    main["cycle driver"]["end time units"] = "yr"
    main["cycle driver"]["required times"]["times start period stop"] = ats_input_spec.public.time_in_seconds([0, 1, -1], 'd')

    # checkpoint yearly
    main["checkpoint"]["times start period stop"] = ats_input_spec.public.time_in_seconds([0,1,-1], 'yr')

    # vis daily
    ats_input_spec.public.add_to_all_visualization(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,1,-1], 'd'))
    return main
    
def test_writing(main):
    ats_input_spec.io.write(main, 'ats_input_spec/tests/out.xml')

    with open('ats_input_spec/tests/out_gold.xml', 'r') as fid:
        lines_gold = fid.read()

    with open('ats_input_spec/tests/out.xml', 'r') as fid:
        lines = fid.read()

    assert(lines_gold == lines)
        
    
