"""ats_input_spec/base.py

ATS is released under the three-clause BSD License. 
The terms of use and "as is" disclaimer for this license are 
provided in the top-level COPYRIGHT file.

Authors: Ethan Coon (ecoon@lanl.gov)

Colors used for pretty printing.

Changing these here changes them everywhere!

"""


import colorama

NAME = colorama.Fore.CYAN
FILLED = colorama.Fore.GREEN
DEFAULT = colorama.Fore.YELLOW
UNFILLED = colorama.Fore.RED

RESET = colorama.Fore.RESET


def indent(string, ntabs=1, spaces_per=2):
    return '\n'.join([' '*(spaces_per*ntabs)+line for line in string.split('\n')])
