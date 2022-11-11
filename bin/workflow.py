import ats_input_spec
import ats_input_spec.public


main = ats_input_spec.public.get_main()
poro_eval = main['state']['field evaluators'].append_empty('base_porosity')
poro_eval.set_type('independent variable', ats_input_spec.public.known_specs['independent-variable-evaluator-spec'])
poro_eval['constant in time'] = True


def add_region_set_value(evaluator, ats_id, val):
    region = f'glyhymps-{ats_id}'
    my_func = evaluator['function'].append_empty(region)
    my_func['region'] = region
    my_func['component'] = 'CELL'
    my_func_const = my_func['function'].set_type('constant', ats_input_spec.public.known_specs['function-constant-spec'])
    my_func_const['value'] = float(val)

add_region_set_value(poro_eval, 1001, 0.25)
print(poro_eval)


