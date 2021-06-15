"""ats_input_spec/public.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (coonet@ornl.gov)

The public interface of the ats_input_spec package.

"""

import ats_input_spec.specs
import ats_input_spec.source_reader

known_specs = ats_input_spec.source_reader.load()

def get_main():
    """Gets the top level spec and all non-optional sub-specs."""
    global known_specs
    return known_specs["main-spec"]

def add_domain(main, domain_name, dimension, mesh_type, mesh_args=None):
    """Adds objects associated with a domain.

    Arguments:
      mesh_list         | list to add domain to
      domain_name       | name this domain
      dimension         | 3 if a subsurface mesh, 
                        |  2 if a surface mesh
      mesh_type         | One of: "generate mesh", "read mesh file",
                        |  "logical", "surface", "subgrid", or 
                        |  "column".

    Adds:
      - placeholders for a mesh
      - placeholders for a visualization list
      - a region for the entirety of that domain.

    """
    global known_specs

    if mesh_args is None:
        mesh_args = dict()

    # add the mesh
    new_mesh = main['mesh'].append_empty(domain_name)
    mesh_type_spec = ats_input_spec.source_reader.to_specname('mesh '+mesh_type)
    new_mesh.set_type(mesh_type, known_specs[mesh_type_spec])
    new_mesh[mesh_type+' parameters'].update(mesh_args) 

    # add a dimension-sized region of large extent for "all"
    region_name = ''
    if domain_name == "domain":
        region_name = "computational domain"
    else:
        region_name = "%s domain"%domain_name
    add_region(main, region_name, 'all')

    # add a visualization sublist for this domain
    main['visualization'].append_empty(domain_name)
    return new_mesh

def add_region(main, region_name, region_type, region_args=None):
    """Adds objects associated with a region.

    Arguments:
      region_list       | list to add region
      region_name       | name this region
      region_spec       | spec of the region, of the form "region-box" or "region-planar"
      region_pars       | Dictionary of extra parameters needed by the spec.
    """
    global known_specs

    region_list = main['regions']
    if region_args is None:
        region_args = dict()
    new_region = region_list.append_empty(region_name)
    region_type_spec = ats_input_spec.source_reader.to_specname('region '+region_type)
    new_region.set_type(region_type, known_specs[region_type_spec])
    new_region.get_sublist().update(region_args)
    return new_region

def add_to_all_visualization(main, io_parameter_name, io_value, io_units=None):
    """Adds a visualization parameter to all vis specs. 

    This makes it easier to vis all domains at the same times (which
    is typically what is desired).  Example usage:

    # daily vis
    add_to_all_visualization(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,1,-1], 'd'))
    """
    for vis in main["visualization"].values():
        vis[io_parameter_name] = io_value
        if io_units is not None:
            vis[io_parameter_name+' units'] = io_units
    
def time_in_seconds(value, units):
    """Convenient converter for time in seconds"""
    unit_conv = dict(s=1, hr=3600, d=86400, yr=86400*365)

    if type(value) is float or type(value) is int:
        return value * unit_conv[units]
    else:
        return [v*unit_conv[units] for v in value]
    
def set_typical_constants(main):
    """Sets atmospheric pressure and gravity, which are basically in everything."""
    global known_specs
    atmos = ats_known_specs["constants-scalar-spec"]
    atmos["value"] = 101325.0
    main["state"]["initial conditions"]["atmospheric pressure"] = atmos

    grav = known_specs["constants-vector-spec"]
    grav["value"] = [0.,0.,-9.80665]
    main["state"]["initial conditions"]["gravity"] = grav

def add_observation(main, name, obs_args=None):
    """Adds an observation of a given variable.

    Options can be provided in an dictionary, obs_args"""
    obs = main['observations'].append_empty(name)
    obs.update(obs_args)
    return obs

def add_to_all_observations(main, io_parameter_name, io_value, io_units):
    """Adds a visualization parameter to all vis specs. 

    This makes it easier to vis all domains at the same times (which
    is typically what is desired).  Example usage:

    # daily vis
    add_to_all_observations(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,1,-1], 'd'))
    """
    for obs in main["observations"].values():
        obs[io_parameter_name] = io_value
        if io_units is not None:
            obs[io_parameter_name+' units'] = io_units

def add_leaf_pk(main, name, parent_list, pk_type):
    """Adds a PK... time to break something!"""
    global known_specs
    
    # add the tree entry, and pop the sub PKs list which is not needed for leaf PKs
    pk_tree_entry = parent_list.append_empty(name)
    pk_tree_entry.set_type(pk_type, known_specs[pk_type])

    # add the PKs entry
    pk_type_spec = pk_type.replace(" ","-")+"-spec"
    pk_entry = known_specs[pk_type_spec]
    main["PKs"][name] = pk_entry
    return pk_entry
    
    
def set_pk_evaluator_requirements(main, pk):
    """Ensures evaluator requirements of each PK are in the evaluator list."""
    
    for req in pk.eval_reqs:
        # find the name needed
        if req+" key" in pk.keys():
            name = pk[req+" key"]
        else:
            suffix_name = req+" suffix"
            if suffix_name in pk.keys():
                suffix = pk[req+" suffix"]
            else:
                suffix = pk.spec[suffix_name].default
                assert(suffix is not None)                
                
            domain = pk["domain name"]
            if domain != "domain" and domain != "":
                name = domain+"-"+suffix
            else:
                name = suffix

        if name not in main["state"]["field evaluators"].keys():
            main["state"]["field evaluators"].append_empty(name)
        
        
