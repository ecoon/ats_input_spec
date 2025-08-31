"""ats_input_spec/solvers.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (coonet@ornl.gov)

Provides some basic solvers.

"""
from ats_input_spec.public import known_specs
import ats_input_spec.specs

def add_inverse_ILU_GMRES(pk_list):
    """Adds GMRES with block ILU preconditioner"""
    pk_list["inverse"]["preconditioning method"] = "block ilu"
    pk_list["inverse"]["iterative method"] = "gmres"

    # this call is special because gmres parameters is not in the spec
    # (this is not a typed spec or it would be)
    pk_list["inverse"].append(ats_input_spec.specs.SpecDict({"gmres parameters" :
                                                             known_specs["iterative-method-gmres-spec"]}))
    pk_list["inverse"]["gmres parameters"].update({"error tolerance" : 1.e-6,
                                                   "maximum number of iterations" : 10})

def add_solver_nka_bt_ats(pk_list):
    pk_list["time integrator"]["solver type"] = "nka_bt_ats"

    # this call is special because nka_bt_ats parameters is not in the spec
    # (this is not a typed spec or it would be)
    pk_list["time integrator"].append(ats_input_spec.specs.SpecDict({"nka_bt_ats parameters" :
                                                                     known_specs["solver-nka-bt-ats-spec"]}))

    pk_list["time integrator"]["nka_bt_ats parameters"].update({"nka lag iterations" : 2,
                                                                "backtrack max steps" : 5,
                                                                "backtrack tolerance" : 1.e-4,
                                                                "nonlinear tolerance" : 1.e-5,
                                                                "diverged tolerance" : 1.e5,
                                                                })

    
def add_time_integrator_smarter(pk_list):
    """Adds a default 'smarter' time integrator."""
    pk_list["time integrator"]["extrapolate initial guess"] = True
    pk_list["time integrator"]["timestep controller type"] = "smarter"
    pk_list["time integrator"].append(ats_input_spec.specs.SpecDict({"timestep controller smarter parameters" :
                                                                     known_specs["timestep-controller-smarter-spec"]}))
    pk_list["time integrator"]["timestep controller smarter parameters"].update({"max iterations" : 18,
                                                                                 "min iterations" : 7,
                                                                                 "timestep increase factor" : 1.25,
                                                                                 "timestep reduction factor" : 0.7,
                                                                                 "growth wait after fail" : 2,
                                                                                 "count before increasing increase factor" : 2,
                                                                                 "max timestep [s]" : 1e10,
                                                                                 "min timestep [s]" : 1e-10,
                                                                                 })
                                                                
