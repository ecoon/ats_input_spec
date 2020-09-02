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


@pytest.fixture
def main():
    ats_input_spec.known_specs.load()
    yield ats_input_spec.public.get_main()
    ats_input_spec.known_specs.clear()

def test_get_main(main):
    pass

def test_add_domain(main):
    # add a mesh
    mesh_args = {"file":"../mymesh.exo"}
    ats_input_spec.public.add_domain(main, "domain", 3, "read mesh file", mesh_args)

    # end after one year, require daily syncronization
    main["cycle driver"]["end time"] = 1.0
    main["cycle driver"]["end time units"] = "yr"
    main["cycle driver"].fill_default("required times")
    main["cycle driver"]["required times"]["times start period stop"] = ats_input_spec.public.time_in_seconds([0, 1, -1], 'd')

    # checkpoint yearly
    main["checkpoint"]["times start period stop"] = ats_input_spec.public.time_in_seconds([0,1,-1], 'yr')

    # vis daily
    ats_input_spec.public.add_to_all_visualization(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,1,-1], 'd'))

    # # add atmospheric pressure and gravity
    # ats_input_spec.public.set_typical_constants(main)

    # # add an observation
    # obs_pars = {"variable":"water_content", "observation output filename":"total_water_content.txt",
    #             "region":"domain", "location name":"cell", "functional":"observation data: extensive integral"}
    # ats_input_spec.public.add_observation(main, "total_water_content", obs_pars)
    # ats_input_spec.public.add_to_all_observations(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,0.1,-1], 'd'))

    # # add a PK
    # ats_input_spec.public.add_leaf_pk(main, "subsurface flow", main["cycle driver"]["PK tree"], "richards")
    ats_input_spec.printing.help('main', main)
