import rethink.printing
import rethink.public

main = rethink.public.get_main()

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

# add atmospheric pressure and gravity
rethink.public.set_typical_constants(main)

# add an observation
obs_pars = {"variable":"water_content", "observation output filename":"total_water_content.txt",
            "region":"domain", "location name":"cell", "functional":"observation data: extensive integral"}
rethink.public.add_observation(main, "total_water_content", obs_pars)
rethink.public.add_to_all_observations(main, "times start period stop", rethink.public.time_in_seconds([0,0.1,-1], 'd'))

# print the result
rethink.printing.help('main', main, False)

# add a PK
leaf = rethink.public.add_leaf_pk(main, "subsurface flow", main["cycle driver"]["PK tree"], "richards")
leaf['primary variable key'] = 'pressure'
leaf['domain name'] = ""
print("="*80)
rethink.printing.help('subsurface flow', leaf, True)

# ensure PK's evaluator needs are there
rethink.public.set_pk_evaluator_requirements(main, leaf)
print("="*80)
rethink.printing.help('main', main, False)

import rethink.xml.to_xml
xml = rethink.xml.to_xml.to_xml(main)

# from rethink.xml import etree
# xml_bstr = etree.tostring(xml, pretty_print=True)
# for line in xml_bstr.split(b"\n"):
#     print(line)

# xml.write("out.xml", pretty_print=True)
