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

#
# Main is the top level list
# 
def get_main():
    """Gets the top level spec and all non-optional sub-specs."""
    global known_specs
    return known_specs["main-spec"]


#
# Domains correspond to meshes, but also include vis, regions, etc.
#
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
        region_name = f"{domain_name} domain"
    add_region(main, region_name, 'all')
    add_region(main, region_name+' boundary', 'boundary', {'entity':'FACE'})

    # add a visualization sublist for this domain
    main['visualization'].append_empty(domain_name)
    return new_mesh


#
# Regions are subsets of discrete entities on a mesh, sometimes
# defined by lists of entities that are labeled in the mesh file,
# sometimes defined by geometric extents that are intersected with
# entity centroids.  Add a region to the input file.
#
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
    if region_type == 'all':
        # ugly hack to keep this required but empty list from disappearing...
        region_args['empty'] = True
    new_region.get_sublist().update(region_args)
    return new_region

def add_region_labeled_set(main, region_name, label, filename, entity_kind):
    """Helper function to add labeled sets to the main list"""
    return add_region(main, region_name, 'labeled set', 
                      region_args={'label' : str(label), 
                                   'file' : filename,
                                   'format' : 'Exodus II',
                                   'entity' : entity_kind})

#
# Helper functions for visualization
#
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

#
# State's "initial conditions" list, set defaults (atmospheric pressure and gravity)
#
def set_typical_constants(main):
    """Sets atmospheric pressure and gravity, which are basically in everything."""
    global known_specs
    atmos = known_specs["constants-scalar-spec"]
    atmos["value"] = 101325.0
    main["state"]["initial conditions"]["atmospheric pressure"] = atmos

    grav = known_specs["constants-vector-spec"]
    grav["value"] = [0.,0.,-9.80665]
    main["state"]["initial conditions"]["gravity"] = grav

def set_land_cover_default_constants(main, land_cover_name):
    """Adds an empty land cover list, and populates it with "standard" default values."""
    try:
        lc_list = main['state']['initial conditions']['land cover types']
    except KeyError:
        lc_list = known_specs['land-cover-spec-list']
        main['state']['initial conditions']['land cover types'] = lc_list

    lc = lc_list.append_empty(land_cover_name)

    # set some basic defaults
    lc['Priestley-Taylor alpha of snow [-]'] = 1.26
    lc['Priestley-Taylor alpha of bare ground [-]'] = 1.26
    lc['Priestley-Taylor alpha of canopy [-]'] = 1.26
    lc['Priestley-Taylor alpha of transpiration [-]'] = 1.26

    lc['albedo of bare ground [-]'] = 0.4
    lc['emissivity of bare ground [-]'] = 0.98
    lc['albedo of canopy [-]'] = 0.11
    lc['emissivity of canopy [-]'] = 0.95
    
    lc["Beer's law extinction coefficient, shortwave [-]"] = 0.6
    lc["Beer's law extinction coefficient, longwave [-]"] = 5
    
    lc["snow transition depth [m]"] = 0.02
    lc["dessicated zone thickness [m]"] = 0.1
    lc["Clapp and Hornberger b [-]"] = 1
    
    # defaults for grass/no vei
    lc['rooting depth max [m]'] = 5.
    lc['rooting profile alpha [-]'] = 11.0
    lc['rooting profile beta [-]'] = 2.0

    # Note, the mafic potential values are likely pretty bad for the types of van Genuchten 
    # curves we are using (https://www.sciencedirect.com/science/article/pii/S0168192314000483).
    # Likely they need to be modified.  Note that these values are in [mm] from CLM TN 4.5 table 8.1, so the 
    # factor of 10 converts to [Pa].
    #
    # instead of using a factor of 10, we use a factor of 1 for closed and .1 for open to make this more 
    # physically viable for our VG models
    lc['mafic potential at fully closed stomata [Pa]'] = 275000.
    lc['mafic potential at fully open stomata [Pa]'] = 74000. * .1
    
    # by default we let the LAI take care of this rather than turn off deciduous 
    # transpiration manually the way that PRMS does it. 
    lc['leaf on time [doy]'] = -1
    lc['leaf off time [doy]'] = -1
    return lc

#
# Add an observation file, which is a collection of observables to be
# saved at the same times.
#
def add_observation(main, name, filename,
                    delimiter=',', time_units='s',
                    obs_args=None):
    """Adds an empty observation spec.

    Extra options such as "time start period stop" can be provided in
    an dictionary, obs_args
    """
    obs = main['observations'].append_empty(name)

    obs_args_l = {'delimiter':delimiter,
                  'observation output filename':filename,
                  'time units':time_units}
    if obs_args is not None:
        obs_args_l.update(obs_args)
    obs.update(obs_args_l)
    return obs

def add_observeable(obs, name, variable, region, functional, entity_type,
                    time_integrated=False, obs_args=None):
    """Adds an observable to a given observation file."""
    observ = obs['observed quantities'].append_empty(name)
    observ['variable'] = variable
    if type(region) is str:
        observ['region'] = region
    else:
        observ['regions'] = region
    observ['functional'] = functional
    observ['location name'] = entity_type
    observ['time integrated'] = time_integrated

    if obs_args is not None:
        observ.update(obs_args)
    return observ

def add_to_all_observations(main, io_parameter_name, io_value, io_units):
    """Adds a visualization parameter to all vis specs. 

    This makes it easier to vis all domains at the same times (which
    is typically what is desired).  Example usage:

    # daily vis
    add_to_all_observations(main, "times start period stop", 
                ats_input_spec.public.time_in_seconds([0,1,-1], 'd'))
    """
    for obs in main["observations"].values():
        obs[io_parameter_name] = io_value
        if io_units is not None:
            obs[io_parameter_name+' units'] = io_units

def add_observations_water_balance(main, region,
                                   surface_region=None,
                                   boundary_region=None,
                                   surface_boundary_region=None,
                                   outlet_region=None,
                                   has_canopy=True, time_args=None):
    region_us = region.replace(' ', '_')
    if surface_region is None:
        surface_region = region
    if boundary_region is None:
        boundary_region = region + ' boundary'
    if surface_boundary_region is None:
        surface_boundary_region = surface_region + ' boundary'
    if outlet_region is None:
        outlet_region = surface_region + ' outlet'

    name = f'water_balance_{region_us}'
    if time_args is None:
        time_args = {'times start period stop':[0.,1.,-1.],
                     'times start period stop units':'d'}

    # add the observation
    obs = add_observation(main, name, name+'.csv', time_units='d', obs_args=time_args)

    # add observables
    # - net runoff - runon
    observ1 = add_observeable(obs, 'net runoff [mol d^-1]', 'surface-mass_flux', surface_boundary_region,
                             'extensive integral', 'face', time_integrated=True)
    observ1['direction normalized flux'] = True
    if region != 'computational domain':
        observ1['direction normalized flux relative to region'] = surface_region

    # - runoff from the outlet
    observ2 = add_observeable(obs, 'river discharge [mol d^-1]', 'surface-mass_flux', outlet_region,
                             'extensive integral', 'face', time_integrated=True)
    observ2['direction normalized flux'] = True
    if region != 'computational domain':
        observ1['direction normalized flux relative to region'] = surface_region

    # - subsurface groundwater net gain/loss
    observ3 = add_observeable(obs, 'net groundwater flux [mol d^-1]', 'mass_flux', boundary_region,
                             'extensive integral', 'face', time_integrated=True)
    observ3['direction normalized flux'] = True
    if region != 'computational domain':
        observ1['direction normalized flux relative to region'] = region

    
    # - surface average quantities
    flux_to_obs = [('surface-precipitation_rain','rain precipitation [m d^-1]'),
                   ('snow-precipitation', 'snow precipitation [m d^-1]'),
                   ('surface-air_temperature', 'air temperature [K]'),
                   ('surface-relative_humidity', 'relative humidity [-]'),
                   ('surface-incoming_shortwave_radiation', 'incoming shortwave radiation [W m^-2]'),
                   ('surface-evaporation', 'surface evaporation [m d^-1]'),
                   ('snow-evaporation', 'snow evaporation [m d^-1]'),
                   ('surface-transpiration', 'transpiration [m d^-1]'),
                   ('snow-melt', 'snowmelt [m d^-1]'),
                   ('surface-surface_subsurface_flux', 'infiltration [mol d^-1]'),]
    ext_to_obs = [('surface-water_content', 'surface water content [mol]'),
                  ('snow-water_content', 'snow water content [mol]'),]

    if has_canopy:
        flux_to_obs.extend([('canopy-evaporation', 'canopy evaporation [m d^-1]'),])
        ext_to_obs.extend([('canopy-water_content', 'canopy water content [mol]'),])

    for flux_obs_var, flux_obs_name in flux_to_obs:
        add_observeable(obs, flux_obs_name, flux_obs_var, surface_region,
                        'average', 'cell', True)
    for ext_obs_var, ext_obs_name in ext_to_obs:
        add_observeable(obs, ext_obs_name, ext_obs_var, surface_region,
                        'extensive integral', 'cell')
    add_observeable(obs, 'subsurface water content [mol]', 'water_content', region,
                    'extensive integral', 'cell')
              
    
    return obs


#
# PK objects -- not particularly well supported yet!
#
def add_leaf_pk(main, name, parent_list, pk_type):
    """Adds a PK... time to break something!"""
    global known_specs
    
    # add the tree entry, and pop the sub PKs list which is not needed for leaf PKs
    pk_tree_entry = parent_list.append_empty(name)
    pk_tree_entry.set_type(pk_type, known_specs[pk_type])

    # add the PKs entry
    pk_entry = main["PKs"].append_empty(name)
    pk_entry.set_type('richards', known_specs[pk_type])
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


#
# evaluators
#
def add_daymet_point_evaluators(main, daymet_filename):
    """Adds the "standard" DayMet evaluators, based on a given file.

    This includes the following evaluators:
    - surface-precipitation_rain
    - snow-precipitation
    - surface-incoming_shortwave_radiation
    - surface-air_temperature
    - surface-relative_humidity
    """
    global known_specs
    
    daymet_vars = [('surface-precipitation_rain','precipitation rain [m s^-1]'),
                   ('snow-precipitation','precipitation snow [m SWE s^-1]'),
                   ('surface-air_temperature','air temperature [K]'),
                   ('surface-relative_humidity','relative humidity [-]'),
                   ('surface-incoming_shortwave_radiation','incoming shortwave radiation [W m^-2]'),
                   ]
    for var, name in daymet_vars:
        ev = main['state']['field evaluators'].append_empty(var)
        ev.set_type('independent variable', known_specs['independent-variable-evaluator-spec'])
        entry = ev['function'].append_empty('surface domain')
        entry['region'] = 'surface domain'
        entry['component'] = 'cell'
        ft = entry['function'].set_type('tabular', known_specs['function-tabular-fromfile-spec'])
        ft['file'] = daymet_filename
        ft['x header'] = 'time [s]'
        ft['y header'] = name
        

def add_daymet_box_evaluators(main, daymet_filename):
    """Adds the "standard" DayMet evaluators on a raster box, based on a given file.

    This includes the following evaluators:
    - surface-precipitation_rain
    - snow-precipitation
    - surface-incoming_shortwave_radiation
    - surface-air_temperature
    - surface-relative_humidity
    """
    daymet_vars = [('surface-precipitation_rain','precipitation rain [m s^-1]'),
                   ('snow-precipitation','precipitation snow [m SWE s^-1]'),
                   ('surface-air_temperature','air temperature [K]'),
                   ('surface-relative_humidity','relative humidity [-]'),
                   ('surface-incoming_shortwave_radiation','incoming shortwave radiation [W m^-2]'),
                   ]
    for var, name in daymet_vars:
        ev = main['state']['field evaluators'].append_empty(var)
        ev.set_type('independent variable', known_specs['independent-variable-evaluator-spec'])
        entry = ev['function'].append_empty('surface domain')
        entry['region'] = 'surface domain'
        entry['component'] = 'cell'
        ft = entry['function'].set_type('bilinear-and-time',
                                        known_specs['function-bilinear-and-time-spec'])
        ft['file'] = daymet_filename
        ft['row header'] = 'y [m]'
        ft['column header'] = 'x [m]'
        ft['row coordinate'] = 'y'
        ft['column coordinate'] = 'x'
        ft['time header'] = 'time [s]'
        ft['value header'] = name

def add_soil_type(main, region_name, label=None, filename=None, porosity=None, permeability=None, compressibility=None,
                  van_genuchten_alpha=None, van_genuchten_n=None, residual_sat=None, smoothing_interval=None,
                  porosity_key='base_porosity', permeability_key='permeability', compressibility_key='porosity',
                  wrm_key='saturation_liquid'):
    """Adds a region plus assorted soil property entries associated with that region."""
    # add the region
    if label != None and filename != None:
        add_region_labeled_set(main, region_name, label, filename, 'CELL')

    def add_entry(key, value):
        try:
            fe = main['state']['field evaluators'][key]
        except KeyError:
            fe = main['state']['field evaluators'].append_empty(key)
            fe.set_type('independent variable', known_specs['independent-variable-evaluator-spec'])
            fe['constant in time'] = True
        sublist = fe['function'].append_empty(region_name)
        sublist['region'] = region_name
        sublist['component'] = 'cell'
        entry = sublist['function'].set_type('constant', known_specs['function-constant-spec'])
        entry['value'] = value

    # add porosity & permeability
    if porosity is not None:
        add_entry('base_porosity', porosity)
    if permeability is not None:
        add_entry('permeability', permeability)

    # add the entry for pore compressibility
    if compressibility is not None:
        try:
            fe = main['state']['field evaluators'][compressibility_key]
        except KeyError:
            fe = main['state']['field evaluators'].append_empty(compressibility_key)
            fe.set_type('compressible porosity', known_specs['compressible-porosity-evaluator-spec'])
        sublist = fe['compressible porosity model parameters'].append_empty(region_name)
        sublist['region'] = region_name
        sublist['pore compressibility [Pa^-1]'] = compressibility

    # add the entry for WRM
    if van_genuchten_alpha is not None and van_genuchten_n is not None and residual_sat is not None:
        wrm = main['PKs']['flow']['water retention evaluator']['WRM parameters']
        sublist = wrm.append_empty(region_name)
        sublist = sublist.set_type('van Genuchten', known_specs['WRM-van-Genuchten-spec'])
        sublist['region'] = region_name
        sublist['van Genuchten alpha [Pa^-1]'] = van_genuchten_alpha
        sublist['van Genuchten n [-]'] = van_genuchten_n
        sublist['residual saturation [-]'] = residual_sat
        if smoothing_interval is not None:
            sublist['smoothing interval width [saturation]'] = smoothing_interval
        
        
    
    
                  
