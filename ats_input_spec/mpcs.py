"""ats_input_spec/mpc.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (coonet@ornl.gov)

Provides some MPC filling

"""


def add_mpc_water_delegate(mpc_list):
    mpc_list["water delegate"]["modify predictor damp and cap the water spurt"] = True
    mpc_list["water delegate"]["damp and cap the water spurt"] = True
    mpc_list["water delegate"]["cap over atmospheric"] = 0.001
    
