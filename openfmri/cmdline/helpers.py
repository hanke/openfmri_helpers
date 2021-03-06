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

import argparse
import re
import sys
import os
from os.path import join as opj
import logging
lgr = logging.getLogger(__name__)


class HelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if option_string == '--help':
            # lets use the manpage on mature systems ...
            try:
                import subprocess
                subprocess.check_call(
                    'man %s 2> /dev/null' % parser.prog.replace(' ', '-'),
                    shell=True)
                sys.exit(0)
            except (subprocess.CalledProcessError, OSError):
                # ...but silently fall back if it doesn't work
                pass
        if option_string == '-h':
            helpstr = "%s\n%s" % \
                (parser.format_usage(),
                 "Use '--help' to get more comprehensive information.")
        else:
            helpstr = parser.format_help()
        # better for help2man
        helpstr = re.sub(r'optional arguments:', 'options:', helpstr)
        helpstr = re.sub(r'positional arguments:\n.*\n', '', helpstr)
        # convert all heading to have the first character uppercase
        headpat = re.compile(r'^([a-z])(.*):$', re.MULTILINE)
        helpstr = re.subn(headpat,
                          lambda match: r'{0}{1}:'.format(match.group(1).upper(),
                                                          match.group(2)),
                          helpstr)[0]
        # usage is on the same line
        helpstr = re.sub(r'^usage:', 'Usage:', helpstr)
        if option_string == '--help-np':
            usagestr = re.split(r'\n\n[A-Z]+', helpstr, maxsplit=1)[0]
            usage_length = len(usagestr)
            usagestr = re.subn(r'\s+', ' ', usagestr.replace('\n', ' '))[0]
            helpstr = '%s\n%s' % (usagestr, helpstr[usage_length:])
        print helpstr
        sys.exit(0)


def parser_add_common_args(parser, pos=None, opt=None, **kwargs):
    from . import common_args
    for i, args in enumerate((pos, opt)):
        if args is None:
            continue
        for arg in args:
            arg_tmpl = getattr(common_args, arg)
            arg_kwargs = arg_tmpl[2].copy()
            arg_kwargs.update(kwargs)
            if i:
                parser.add_argument(*arg_tmpl[i], **arg_kwargs)
            else:
                parser.add_argument(arg_tmpl[i], **arg_kwargs)


def parser_add_common_opt(parser, opt, names=None, **kwargs):
    from . import common_args
    opt_tmpl = getattr(common_args, opt)
    opt_kwargs = opt_tmpl[2].copy()
    opt_kwargs.update(kwargs)
    if names is None:
        parser.add_argument(*opt_tmpl[1], **opt_kwargs)
    else:
        parser.add_argument(*names, **opt_kwargs)

def get_cfg_option(section, optname, cli_input=None, default=None):
    """Determine configuration option value.

    If there was input from the command line it takes precedence. Otherwise
    a pre-configured option value is returned. If neither of them is available
    ``default`` is returned.

    Parameters
    ----------
    section : str
      Configuration section name.
    optname : str
      Option name
    cli_input
      Potential input from a corresponding command line option
    default :
      Value to return if no information is available
    """
    from openfmri import cfg
    if not cli_input is None:
        # got something meaningful as a commandline arg -- got with it
        lgr.debug("using cmdline input '%s' for option '%s[%s]'"
                  % (cli_input, section, optname))
        return cli_input
    if cfg.has_section(section) and cfg.has_option(section, optname):
        val = cfg.get(section, optname)
        lgr.debug("using generic configuration '%s' for option '%s[%s]'"
                  % (val, section, optname))
        return val
    lgr.debug("using default configuration '%s' for build option '%s[%s]'"
               % (default, section, optname))
    return default


def get_path_cfg(section, option, cli_input, default=None,
                 ensure_exists=False, create_dir=False):
    """Specialized frontend for options that specify paths.

    Parameters
    ----------
    section : str
      Configuration section name.
    option : str
      Name of the option
    cmdline_input : any
      Value given via cmdline option
    default :
      Value to return if no information is available
    ensure_exists : bool
      If True, verify that the given path exists, or raise an exceptioni
      otherwise.
    create_dir : bool
      If True, create a directory for the given path if it does not exist yet.
    """
    path_ = get_cfg_option(section, option, cli_input, default)
    if path_ is None:
        if ensure_exists:
            raise ValueError(
                "path for '%s[%s]' not configured, but is required to exist"
                % (section, option))
        return path_
    path_ = os.path.expanduser(os.path.expandvars(path_))
    lgr.debug("path for '%s[%s]' set to '%s'" % (section, option, path_))
    if ensure_exists and not os.path.exists(path_):
        if create_dir:
            lgr.debug("create directory '%s' for '%s[%s]'"
                      % (path_, section, option))
            os.makedirs(path_)
        else:
            raise ValueError(
                "path '%s' for '%s[%s]' is required to exist, but does not"
                % (path_, section, option))
    return path_

def arg2bool(arg):
    if arg in (True, False, None):
        return arg
    arg = arg.lower()
    if arg in ['0', 'no', 'off', 'disable', 'false']:
        return False
    elif arg in ['1', 'yes', 'on', 'enable', 'true']:
        return True
    else:
        raise argparse.ArgumentTypeError(
                "'%s' cannot be converted into a boolean" % arg)

def get_base_workflow(name, args):
    import nipype.pipeline.engine as pe
    wdir = get_path_cfg('common', 'work directory',
                        cli_input=args.workdir,
                        default=opj(os.path.curdir, 'pipe_tmp'),
                        ensure_exists=True,
                        create_dir=True)

    wf = pe.Workflow(name=name)
    wf.base_dir = os.path.abspath(wdir)
    wf.config['execution'] = {
        'stop_on_first_crash': 'True',}
    ##        'hash_method': 'timestamp'}
    return wf

def get_data_src(name, args, basedir, outfields, field_template,
                 template_args=None):
    import nipype.interfaces.io as nio
    import nipype.pipeline.engine as pe

    # data source config
    data = nio.DataGrabber(outfields=outfields)
    data.inputs.template = '*'
    data.inputs.sort_filelist = True
    data.inputs.base_directory = os.path.abspath(basedir)
    data.inputs.field_template = field_template
    if not template_args is None:
        data.inputs.template_args = template_args
    datasrc = pe.Node(name=name, interface=data)
    return datasrc

def get_data_finder(name, basedir, match_regex, ignore_regexes=None):
    import nipype.interfaces.io as nio
    import nipype.pipeline.engine as pe
    df = nio.DataFinder()
    df.inputs.root_paths = basedir
    df.inputs.match_regex = match_regex
    lgr.debug("configuring data finder: basepath '%s', match_regex '%s'"
                      % (basedir, match_regex))
    if not ignore_regexes is None:
        df.inputs.ignore_regexes = ignore_regexes
    datasrc = pe.Node(name=name, interface=df)
    return datasrc

def get_dataset_subj_ids(args):
    if not args.subjects is None:
        subjs = []
        for subj in args.subjects:
            if subj.startswith('sub'):
                subj = subj[3:]
            int_subj = int(subj)
            subjs.append(int_subj)
    else:
        basedir = get_dataset_dir(args)
        subjs = [int(s[3:]) for s in os.listdir(basedir)
                    if s.startswith('sub')
                        and len(s) > 3
                            and s[3].isdigit()]
    return sorted(subjs)

def get_dataset_dir(args):
    datadir = get_path_cfg('common', 'data directory',
                           cli_input=args.datadir,
                           ensure_exists=True)
    dataset = get_cfg_option('common', 'dataset', cli_input=args.dataset)
    return opj(datadir, dataset)

def exclude_subjects(subjects, section):
    exclude = [int(s)
                for s in get_cfg_option(section,
                                        'exclude subjects',
                                        default='').split()]

    lgr.info("exclude subjects '%s' based on configuration'" % exclude)
    return [s for s in subjects if not s in exclude]
