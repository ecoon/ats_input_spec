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
    yield ats_input_spec.public.get_main()

def test_get_main(main):
    pass

def test_add_domain(main):
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

    # # add atmospheric pressure and gravity
    # ats_input_spec.public.set_typical_constants(main)

    # # add an observation
    # obs_pars = {"variable":"water_content", "observation output filename":"total_water_content.txt",
    #             "region":"domain", "location name":"cell", "functional":"observation data: extensive integral"}
    # ats_input_spec.public.add_observation(main, "total_water_content", obs_pars)
    # ats_input_spec.public.add_to_all_observations(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,0.1,-1], 'd'))

    # # add a PK
    # ats_input_spec.public.add_leaf_pk(main, "subsurface flow", main["cycle driver"]["PK tree"], "richards")
    # ats_input_spec.printing.help('main', main)
    print(main)


def test_add_daymet(main):
    ats_input_spec.public.add_daymet_point_evaluators(main, 'mymet.h5')
    print(main)
    assert(main['state']['field evaluators'].is_complete())

def test_add_daymet_box(main):
    ats_input_spec.public.add_daymet_box_evaluators(main, 'mymet.h5')
    print(main)
    assert(main['state']['field evaluators'].is_complete())


def test_add_observation(main):
    obs = ats_input_spec.public.add_observation(main, 'water_balance', 'water_balance.csv', time_units='d',
                                                obs_args={'times start period stop':[0.,1.,-1.],
                                                          'times start period stop units':'d'})
    observ = ats_input_spec.public.add_observeable(obs, 'runoff generation [mol d^-1]', 'surface-mass_flux',
                                                   'surface boundary', 'extensive integral', 'face', True,
                                                   obs_args={'direction normalized flux':True,})
    print(main)
    assert(obs.is_complete())


def test_add_water_balance(main):
    ats_input_spec.public.add_observations_water_balance(main, 'surface domain', 'computational domain', True,
                                                         time_args={'times start period stop':[0.,1.,-1.],
                                                                    'times start period stop units':'d'})
    print(main)
    assert(main['observations'].is_complete())


def test_add_wrm(main):
    # this must work for WRMs to work
    flow_pk = ats_input_spec.public.add_leaf_pk(main, 'flow', main['cycle driver']['PK tree'], 'richards-spec')

    ats_input_spec.public.add_soil_type(main, 'GLHYMPS-10101', '1001', 'myfile.exo',
                                        porosity=0.25, permeability=1.e-12, compressibility=1.e-9,
                                        van_genuchten_alpha=0.0001, van_genuchten_n=1.8, residual_sat=0.1, smoothing_interval=0.01)
    ats_input_spec.public.add_soil_type(main, 'GLHYMPS-10102', '1002', 'myfile.exo',
                                        porosity=0.5, permeability=1.e-10, compressibility=1.e-7,
                                        van_genuchten_alpha=0.0001, van_genuchten_n=1.54, residual_sat=0.05, smoothing_interval=0.01)
    print(main)
    assert(main['state']['field evaluators'].is_complete())
    assert(main['PKs']['flow']['water retention evaluator'].is_complete())


