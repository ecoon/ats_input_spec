import ats_input_spec.known_specs
import ats_input_spec.printing
import ats_input_spec.public

ats_input_spec.known_specs.load()
main = ats_input_spec.public.get_main()

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

# add atmospheric pressure and gravity
ats_input_spec.public.set_typical_constants(main)

# add an observation
obs_pars = {"variable":"water_content", "observation output filename":"total_water_content.txt",
            "region":"domain", "location name":"cell", "functional":"observation data: extensive integral"}
ats_input_spec.public.add_observation(main, "total_water_content", obs_pars)
ats_input_spec.public.add_to_all_observations(main, "times start period stop", ats_input_spec.public.time_in_seconds([0,0.1,-1], 'd'))

# print the result
ats_input_spec.printing.help('main', main, False)

# add a PK
leaf = ats_input_spec.public.add_leaf_pk(main, "subsurface flow", main["cycle driver"]["PK tree"], "richards")
leaf['primary variable key'] = 'pressure'
leaf['domain name'] = ""
print("="*80)
ats_input_spec.printing.help('subsurface flow', leaf, True)

# ensure PK's evaluator needs are there
ats_input_spec.public.set_pk_evaluator_requirements(main, leaf)
print("="*80)
ats_input_spec.printing.help('main', main, False)

import ats_input_spec.xml.to_xml
xml = ats_input_spec.xml.to_xml.to_xml(main)

# from ats_input_spec.xml import etree
# xml_bstr = etree.tostring(xml, pretty_print=True)
# for line in xml_bstr.split(b"\n"):
#     print(line)

# xml.write("out.xml", pretty_print=True)
