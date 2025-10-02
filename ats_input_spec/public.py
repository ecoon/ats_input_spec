"""ats_input_spec/public.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (coonet@ornl.gov)

The public interface of the ats_input_spec package.

"""

import ats_input_spec.specs
from ats_input_spec.specs import DELIMITER
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
    add_region(main, region_name+' boundary', 'boundary')

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


    
def set_land_cover_default_constants(main, land_cover_name, transpiration_model='clm'):
    """Adds an empty land cover list, and populates it with "standard" default values."""
    try:
        lc_list = main['state']['model parameters']['land cover types']
    except KeyError:
        lc_list = known_specs['land-cover-spec-list']
        main['state']['model parameters']['land cover types'] = lc_list

    lc = lc_list.append_empty(land_cover_name)

    # set some basic defaults
    lc['Priestley-Taylor alpha of snow [-]'] = 1.26
    lc['Priestley-Taylor alpha of bare ground [-]'] = 1.26
    lc['Priestley-Taylor alpha of canopy [-]'] = 1.26
    lc['Priestley-Taylor alpha of transpiration [-]'] = 1.26

    lc['albedo of bare ground [-]'] = 0.4
    lc['emissivity of bare ground [-]'] = 0.98
    lc['albedo of canopy [-]'] = 0.11
    
    lc["Beer's law extinction coefficient, shortwave [-]"] = 0.6
    lc["Beer's law extinction coefficient, longwave [-]"] = 5

    if transpiration_model == 'rel perm':
        lc["maximum xylem capillary pressure [Pa]"] = 2240000
    elif transpiration_model == 'clm':
        lc["capillary pressure at fully open stomata [Pa]"] = 3500
        lc["capillary pressure at fully closed stomata [Pa]"] = 224000
    
    lc["snow transition depth [m]"] = 0.02
    
    # defaults for grass/no vei
    lc['rooting depth max [m]'] = 5.
    lc['rooting profile alpha [-]'] = 11.0
    lc['rooting profile beta [-]'] = 2.0

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

def add_observable(obs, name, variable, region, functional, entity_type,
                    time_integrated=False, obs_args=None):
    """Adds an observable to a given observation file."""
    observ = obs['observed quantities'].append_empty(name)
    observ['variable'] = variable
    if type(region) is str:
        observ['region'] = region
    else:
        observ['regions'] = region
    observ['reduction'] = functional
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
                                   has_canopy=True,
                                   time_args=None):
    if surface_region is None:
        surface_region = region+' surface'
    if boundary_region is None:
        boundary_region = region + ' boundary'
    if surface_boundary_region is None:
        surface_boundary_region = boundary_region
    if outlet_region is None:
        outlet_region = surface_region + ' outlet'

    name = f"water_balance_{region.replace(' ', '_')}"
    if time_args is None:
        time_args = {'times start period stop':[0.,1.,-1.],
                     'times start period stop units':'d'}

    # add the observation
    obs = add_observation(main, name, name+'.csv', time_units='d', obs_args=time_args)

    # add observables
    # - net runoff - runon
    observ1 = add_observable(obs, 'net runoff [mol d^-1]', 'surface-water_flux', surface_boundary_region,
                             'extensive integral', 'face', time_integrated=True)
    observ1['direction normalized flux'] = True
    if region != 'computational domain':
        observ1['direction normalized flux relative to region'] = surface_region

    observ1a = add_observable(obs, 'runoff only [mol d^-1]', 'surface-water_flux', surface_boundary_region,
                             'extensive integral', 'face', time_integrated=True)
    observ1a['direction normalized flux'] = True
    mod1a = observ1a['modifier'].set_type('standard math', known_specs['function-standard-math-spec'])
    mod1a['operator'] = 'positive'
    mod1a['amplitude'] = 1.0
    mod1a['shift'] = 0.0

    observ1b = add_observable(obs, 'runon only [mol d^-1]', 'surface-water_flux', surface_boundary_region,
                             'extensive integral', 'face', time_integrated=True)
    observ1b['direction normalized flux'] = True
    mod1b = observ1b['modifier'].set_type('standard math', known_specs['function-standard-math-spec'])
    mod1b['operator'] = 'negative'
    mod1b['amplitude'] = -1.0
    mod1b['shift'] = 0.0
    
    if region != 'computational domain':
        observ1['direction normalized flux relative to region'] = surface_region
        
    # - runoff from the outlet
    observ2 = add_observable(obs, 'river discharge [mol d^-1]', 'surface-water_flux', outlet_region,
                             'extensive integral', 'face', time_integrated=True)
    observ2['direction normalized flux'] = True
    if region != 'computational domain':
        observ2['direction normalized flux relative to region'] = surface_region

    # - subsurface groundwater net gain/loss
    observ3 = add_observable(obs, 'net groundwater flux [mol d^-1]', 'water_flux', boundary_region,
                             'extensive integral', 'face', time_integrated=True)
    observ3['direction normalized flux'] = True
    if region != 'computational domain':
        observ3['direction normalized flux relative to region'] = region
    
    # - surface average quantities
    flux_to_obs = [('surface-precipitation_rain','rain precipitation [m d^-1]'),
                   ('snow-precipitation', 'snow precipitation [m d^-1]'),
                   ('surface-evaporation', 'surface evaporation [m d^-1]'),
                   ('snow-evaporation', 'snow evaporation [m d^-1]'),
                   ('surface-transpiration', 'transpiration [m d^-1]'),
                   ('snow-melt', 'snowmelt [m d^-1]'),
                   ('surface-total_evapotranspiration', 'total evapotranspiration [m d^-1]'),
                   ('surface-surface_subsurface_flux', 'infiltration [mol d^-1]'),
                   ]
    ext_to_obs = [('surface-water_content', 'surface water content [mol]'),
                  ('snow-water_content', 'snow water content [mol]'),
                  ]
    avg_to_obs = [('surface-air_temperature', 'air temperature [K]'),
                  ('surface-incoming_shortwave_radiation', 'incoming shortwave radiation [W m^-2]'),
                  ]

    if has_canopy:
        flux_to_obs.extend([('canopy-evaporation', 'canopy evaporation [m d^-1]'),])
        ext_to_obs.extend([('canopy-water_content', 'canopy water content [mol]'),])

    for flux_obs_var, flux_obs_name in flux_to_obs:
        add_observable(obs, flux_obs_name, flux_obs_var, surface_region,
                        'average', 'cell', True)
    for ext_obs_var, ext_obs_name in ext_to_obs:
        add_observable(obs, ext_obs_name, ext_obs_var, surface_region,
                        'extensive integral', 'cell', False)
    for avg_obs_var, avg_obs_name in avg_to_obs:
        add_observable(obs, avg_obs_name, avg_obs_var, surface_region,
                        'average', 'cell', False)

    add_observable(obs, 'subsurface water content [mol]', 'water_content', region,
                    'extensive integral', 'cell')
    
    return obs


#
# PK objects -- not particularly well supported yet!
#
def add_pk(main, name, pk_type, parent_in_tree):
    """Adds a PK to tree parent_in_tree."""
    global known_specs

    # add the tree entry, and pop the sub PKs list which is not needed for leaf PKs
    pk_tree_entry = parent_in_tree.append_empty(name)
    pk_tree_entry["PK type"] = pk_type

    pk_list_entry = main["PKs"].append_empty(name)
    pk_list_entry.set_type(pk_type, known_specs[f"pk-{pk_type.replace(' ', '-')}-spec"])
    return pk_tree_entry, pk_list_entry
    

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

        if name not in main["state"]["evaluators"].keys():
            main["state"]["evaluators"].append_empty(name)


#
# evaluators
#
def add_daymet_point_evaluators(main, daymet_filename, include_surface_temperature=False):
    """Adds the "standard" DayMet evaluators, based on a given file.

    This includes the following evaluators:
    - surface-precipitation_rain
    - snow-precipitation
    - surface-incoming_shortwave_radiation
    - surface-air_temperature
    - surface-vapor_pressure_air
    """
    global known_specs
    
    daymet_vars = [('surface-precipitation_rain','precipitation rain [m s^-1]'),
                   ('snow-precipitation','precipitation snow [m SWE s^-1]'),
                   ('surface-air_temperature','air temperature [K]'),
                   ('surface-vapor_pressure_air','vapor pressure air [Pa]'),
                   ('surface-incoming_shortwave_radiation','incoming shortwave radiation [W m^-2]'),
                   ]
    for var, name in daymet_vars:
        ev = main['state']['evaluators'].append_empty(var)
        ev.set_type('independent variable', known_specs['evaluator-independent-variable-spec'])
        entry = ev['function'].append_empty('surface domain')
        entry['region'] = 'surface domain'
        entry['component'] = 'cell'
        ft = entry['function'].set_type('tabular', known_specs['function-tabular-fromfile-spec'])
        ft['file'] = daymet_filename
        ft['x header'] = 'time [s]'
        ft['y header'] = name

    if include_surface_temperature:
        # set a surface-temperature as yesterday's air temp
        name = 'air temperature [K]'
        ev = main['state']['evaluators'].append_empty('surface-temperature')
        ev.set_type('independent variable', known_specs['evaluator-independent-variable-spec'])
        entry = ev['function'].append_empty('surface domain')
        entry['region'] = 'surface domain'
        entry['component'] = 'cell'
        ft = entry['function'].set_type('composition', known_specs['function-composition-spec'])

        ft['function1'].set_type('tabular', known_specs['function-tabular-fromfile-spec'])
        ft['function1']['file'] = daymet_filename
        ft['function1']['x header'] = 'time [s]'
        ft['function1']['y header'] = name

        # this function shifts the x-coordinate (time) by 1 day
        ft['function2'].set_type('linear', known_specs['function-linear-spec'])
        ft['function2']['x0'] = [86400.0, 0.0, 0.0]
        ft['function2']['y0'] = 0.
        ft['function2']['gradient'] = [1.0, 0.0, 0.0]
    
        

def add_daymet_box_evaluators(main, daymet_filename, include_surface_temperature=False):
    """Adds the "standard" DayMet evaluators on a raster box, based on a given file.

    This includes the following evaluators:
    - surface-precipitation_rain
    - snow-precipitation
    - surface-incoming_shortwave_radiation
    - surface-air_temperature
    - surface-vapor_pressure_air
    """
    daymet_vars = [('surface-precipitation_rain','precipitation rain [m s^-1]'),
                   ('snow-precipitation','precipitation snow [m SWE s^-1]'),
                   ('surface-air_temperature','air temperature [K]'),
                   ('surface-vapor_pressure_air','vapor pressure air [Pa]'),
                   ('surface-incoming_shortwave_radiation','incoming shortwave radiation [W m^-2]'),
                   ]
    for var, name in daymet_vars:
        ev = main['state']['evaluators'].append_empty(var)
        ev.set_type('independent variable', known_specs['evaluator-independent-variable-spec'])
        entry = ev['function'].append_empty('surface domain')
        entry['region'] = 'surface domain'
        entry['component'] = 'cell'
        ft = entry['function'].set_type('bilinear and time',
                                        known_specs['function-bilinear-and-time-spec'])
        ft['file'] = daymet_filename
        ft['row header'] = 'y [m]'
        ft['column header'] = 'x [m]'
        ft['row coordinate'] = 'y'
        ft['column coordinate'] = 'x'
        ft['time header'] = 'time [s]'
        ft['value header'] = name


    if include_surface_temperature:
        # set a surface-temperature as yesterday's air temp
        name = 'air temperature [K]'
        ev = main['state']['evaluators'].append_empty('surface-temperature')
        ev.set_type('independent variable', known_specs['evaluator-independent-variable-spec'])
        entry = ev['function'].append_empty('surface domain')
        entry['region'] = 'surface domain'
        entry['component'] = 'cell'
        ft = entry['function'].set_type('composition', known_specs['function-composition-spec'])

        ft['function1'].set_type('bilinear and time', known_specs['function-bilinear-and-time-spec'])
        ft['function1']['file'] = daymet_filename
        ft['function1']['row header'] = 'y [m]'
        ft['function1']['column header'] = 'x [m]'
        ft['function1']['row coordinate'] = 'y'
        ft['function1']['column coordinate'] = 'x'
        ft['function1']['time header'] = 'time [s]'
        ft['function1']['value header'] = name

        # this function shifts the x-coordinate (time) by 1 day
        ft['function2'].set_type('linear', known_specs['function-linear-spec'])
        ft['function2']['x0'] = [86400.0, 0.0, 0.0]
        ft['function2']['y0'] = 0.
        ft['function2']['gradient'] = [1.0, 0.0, 0.0]

        
def add_lai_point_evaluators(main, lai_filename, lc_types, crosswalk=None):
    """Adds an LAI time series with one point for each LC type in lc_types"""
    global known_specs
    ev = main['state']['evaluators'].append_empty('canopy-leaf_area_index')
    ev.set_type('independent variable', known_specs['evaluator-independent-variable-spec'])

    is_other = False
    for lc_type in lc_types:
        if lc_type != 'Other':
            entry = ev['function'].append_empty(lc_type)
            entry['region'] = lc_type
            entry['component'] = 'cell'
            func = entry['function'].set_type('tabular', known_specs['function-tabular-fromfile-spec'])
            func['file'] = lai_filename
            func['x header'] = 'time [s]'
            if crosswalk is None:
                func['y header'] = f'{lc_type} LAI [-]'
            else:
                func['y header'] = f'{crosswalk[lc_type]} LAI [-]'
        else:
            is_other = True

    if is_other:
        # other is 0 LAI
        entry_other = ev['function'].append_empty('Other')
        entry_other['region'] = 'Other'
        entry_other['component'] = 'cell'
        entry_other_func = entry_other['function'].set_type('constant', known_specs['function-constant-spec'])
        entry_other_func['value'] = 0.
    

        
def add_soil_type(main, region_name, label=None, filename=None, porosity=None, permeability=None, compressibility=None,
                  van_genuchten_alpha=None, van_genuchten_n=None, residual_sat=None, smoothing_interval=None,
                  porosity_key='base_porosity', permeability_key='permeability', compressibility_key='porosity',
                  wrm_key='saturation_liquid'):
    """Adds a region plus assorted soil property entries associated with that region."""
    # add the region
    if label != None and filename != None:
        add_region_labeled_set(main, region_name, label, filename, 'CELL')

    def add_entry(key, value, tensor=False):
        try:
            fe = main['state']['evaluators'][key]
        except KeyError:
            fe = main['state']['evaluators'].append_empty(key)
            if tensor:
                fe.set_type('independent variable tensor', known_specs['evaluator-independent-variable-tensor-spec'])
                fe['tensor type'] = 'scalar'
            else:
                fe.set_type('independent variable', known_specs['evaluator-independent-variable-spec'])
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
        add_entry('permeability', permeability, True)

    # add the entry for pore compressibility
    if compressibility is not None:
        try:
            fe = main['state']['evaluators'][compressibility_key]
        except KeyError:
            fe = main['state']['evaluators'].append_empty(compressibility_key)
            fe.set_type('compressible porosity', known_specs['evaluator-compressible-porosity-spec'])
        sublist = fe['compressible porosity model parameters'].append_empty(region_name)
        sublist['region'] = region_name
        sublist['pore compressibility [Pa^-1]'] = compressibility

    # add the entry for WRM
    if van_genuchten_alpha is not None and van_genuchten_n is not None and residual_sat is not None:
        try:
            wrm = main['state']['model parameters']['WRM parameters']
        except KeyError:
            wrm = known_specs['wrm-typedinline-spec-list']
            main['state']['model parameters']['WRM parameters'] = wrm

        sublist = wrm.append_empty(region_name)
        sublist = sublist.set_type('van Genuchten', known_specs['wrm-van-genuchten-spec'])
        sublist['region'] = region_name
        sublist['van Genuchten alpha [Pa^-1]'] = van_genuchten_alpha
        sublist['van Genuchten n [-]'] = van_genuchten_n
        sublist['residual saturation [-]'] = residual_sat
        if smoothing_interval is not None:
            sublist['smoothing interval width [saturation]'] = smoothing_interval
        
        
    
    
                  
