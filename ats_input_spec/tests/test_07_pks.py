"""ats_input_spec/public.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Tests for the public interface, solvers.

"""

import pytest
import ats_input_spec.solvers
import ats_input_spec.public


@pytest.fixture
def main():
    yield ats_input_spec.public.get_main()


def test_pk_mpc(main):
    ats_input_spec.public.add_pk(main, "mpc", "weak mpc", main["cycle driver"]["PK tree"])

def test_pk_mpc_solver(main):
    _, mpc_list = ats_input_spec.public.add_pk(main, "mpc", "strong mpc", main["cycle driver"]["PK tree"])
    ats_input_spec.solvers.add_inverse_ILU_GMRES(mpc_list)
    ats_input_spec.solvers.add_solver_nka_bt_ats(mpc_list)
    ats_input_spec.solvers.add_time_integrator_smarter(mpc_list)
    print(mpc_list)
    assert False
    
