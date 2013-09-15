# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the openfmri package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" """

__docformat__ = 'restructuredtext'

# argument spec template
#<name> = (
#    <id_as_positional>, <id_as_option>
#    {<ArgusmentParser.add_arguments_kwargs>}
#)

from os.path import join as opj

from ..cmdline.helpers import HelpAction

help = (
    'help', ('-h', '--help', '--help-np'),
    dict(nargs=0, action=HelpAction,
         help="""show this help message and exit. --help-np forcefully disables
                 the use of a pager for displaying the help.""")
    )

version = (
    'version', ('--version',),
    dict(action='version',
         help="show program's version and license information and exit")
)

datadir = (
    'datadir', ('--datadir',),
    dict(help="""Path of the directory containing all datasets""")
)

dataset = (
    'dataset', ('--dataset',),
    dict(help="""Name of the dataset. This is the name of the sub-directory in
         ``datadir`` that contains the respective dataset.""")
)

task = (
    'task', ('--task',),
    dict(type=int, help="""ID of a task""")
)

workdir = (
    'workdir', ('--workdir',),
    dict(help="""Path of a directory to hold intermediate processing results.""")
)

src_label = (
    'src_label', ('--src-label',),
    dict(help="""Base name of the respective source data files""")
)

label = (
    'label', ('--label',),
    dict(help="""Base name of the respective output data file(s)""")
)

subjects = (
    'subjects', ('--subjects',),
    dict(nargs='*',
         help="""List of IDs of subjects to process.""")
)