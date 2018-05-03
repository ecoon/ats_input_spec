"""rethink/public.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

The public interface of the rethink package.

"""

import rethink.specs
import rethink.known_specs

rethink.known_specs.load()


def get_main():
    """Gets the top level spec and all non-optional sub-specs."""
    return rethink.known_specs.known_specs["simulation-driver-spec"]()

def add_domain(main, domain_name, dimension, mesh_type, mesh_args):
    """Adds objects associated with a domain.

    Arguments:
      main              | main list to add domain to
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
    # add the mesh
    new_mesh = main['mesh'].append_empty(domain_name)
    new_mesh["mesh type"] = mesh_type

    if mesh_type == "read mesh file" and "file" in mesh_args.keys() and "format" not in mesh_args.keys():
        if mesh_args["file"].endswith(".exo") or mesh_args["file"].endswith(".par"):
            mesh_args['format'] = "Exodus II"
        elif mesh_args["file"].endswith(".mstk"):
            mesh_args['format'] = "MSTK"
        else:
            raise RuntimeError('Unknown mesh format from name "%r", please manually set the format.'%mesh_args['file'])
    new_mesh[mesh_type+" parameters"].update(mesh_args) 

    # add a dimension-sized region of large extent for "all"
    region_name = ''
    if domain_name == "domain":
        region_name = "entire domain"
    else:
        region_name = "entire %s domain"%domain_name
    box_pars = {"low coordinate":[-1e80 for i in range(dimension)],
                "high coordinate":[1e80 for i in range(dimension)]}

    add_region(main, region_name, "box", box_pars)

    # add a visualization sublist for this domain
    main['visualization'].append_empty(domain_name)
    return new_mesh

def add_region(main, region_name, region_type, region_args):
    """Adds objects associated with a region.

    Arguments:
      main              | main list to add region
      region_name       | name this region
      region_spec       | spec of the region, of the form "region-box" or "region-planar"
      region_pars       | Dictionary of extra parameters needed by the spec.
    """
    new_region = main['regions'].append_empty(region_name)

    # mangle the spec name into the expected type name
    region_type_name = "region: %s"%region_type
    region_spec_name = "region-%s-spec"%region_type.replace(" ", "-")

    sub_list = rethink.known_specs.known_specs[region_spec_name]()
    new_region[region_type_name] = sub_list
    sub_list.update(region_args)
    return new_region

def add_to_all_visualization(main, io_parameter_name, io_value):
    """Adds a visualization parameter to all vis specs. 

    This makes it easier to vis all domains at the same times (which
    is typically what is desired).  Example usage:

    # daily vis
    add_to_all_visualization(main, "times start period stop", rethink.public.time_in_seconds([0,1,-1], 'd'))
    """
    for vis in main["visualization"].values():
        vis[io_parameter_name] = io_value
    
def time_in_seconds(value, units):
    """Convenient converter for time in seconds"""
    unit_conv = dict(s=1, hr=3600, d=86400, yr=86400*365)

    if type(value) is float or type(value) is int:
        return value * unit_conv[units]
    else:
        return [v*unit_conv[units] for v in value]

def set_typical_constants(main):
    """Sets atmospheric pressure and gravity, which are basically in everything."""
    atmos = rethink.known_specs.known_specs["constants-spec"]()
    atmos["value"] = 101325.0
    main["state"]["initial conditions"]["atmospheric pressure"] = atmos

    grav = rethink.known_specs.known_specs["vector-spec"]()
    grav["value"] = [0.,0.,-9.80665]
    main["state"]["initial conditions"]["gravity"] = grav

def add_observation(main, name, obs_args=None):
    """Adds an observation of a given variable.

    Options can be provided in an dictionary, obs_args"""
    obs = main['observations'].append_empty(name)
    obs.update(obs_args)
    return obs

def add_to_all_observations(main, io_parameter_name, io_value):
    """Adds a visualization parameter to all vis specs. 

    This makes it easier to vis all domains at the same times (which
    is typically what is desired).  Example usage:

    # daily vis
    add_to_all_observations(main, "times start period stop", rethink.public.time_in_seconds([0,1,-1], 'd'))
    """
    for obs in main["observations"].values():
        obs[io_parameter_name] = io_value

def add_leaf_pk(main, name, parent_list, pk_type):
    """Adds a PK... time to break something!"""
    # add the tree entry, and pop the sub PKs list which is not needed for leaf PKs
    pk_tree_entry = parent_list.append_empty(name)
    pk_tree_entry["PK type"] = pk_type

    # add the PKs entry
    pk_type_spec = pk_type.replace(" ","-")+"-spec"
    pk_entry = rethink.known_specs.known_specs[pk_type_spec]()
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
        
        
