"""rethink/public.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Tests for the public interface, full capability.

"""


import pytest
import rethink.public
import rethink.printing


@pytest.fixture
def main():
    return rethink.public.get_main()

def test_get_main(main):
    pass

def test_add_domain(main):
    # add a mesh
    mesh_args = {"file":"../mymesh.exo"}
    rethink.public.add_domain(main, "domain", 3, "read mesh file", mesh_args)

    # end after one year, require daily syncronization
    main["cycle driver"]["end time"] = 1.0
    main["cycle driver"]["end time units"] = "yr"
    main["cycle driver"].fill_default("required times")
    main["cycle driver"]["required times"]["times start period stop"] = rethink.public.time_in_seconds([0, 1, -1], 'd')

    # checkpoint yearly
    main["checkpoint"]["times start period stop"] = rethink.public.time_in_seconds([0,1,-1], 'yr')

    # vis daily
    rethink.public.add_to_all_visualization(main, "times start period stop", rethink.public.time_in_seconds([0,1,-1], 'd'))

    # # add atmospheric pressure and gravity
    # rethink.public.set_typical_constants(main)

    # # add an observation
    # obs_pars = {"variable":"water_content", "observation output filename":"total_water_content.txt",
    #             "region":"domain", "location name":"cell", "functional":"observation data: extensive integral"}
    # rethink.public.add_observation(main, "total_water_content", obs_pars)
    # rethink.public.add_to_all_observations(main, "times start period stop", rethink.public.time_in_seconds([0,0.1,-1], 'd'))

    # # add a PK
    # rethink.public.add_leaf_pk(main, "subsurface flow", main["cycle driver"]["PK tree"], "richards")
    rethink.printing.help('main', main)
