#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Run Corsair from command line with arguments.
"""

import sys
import os
import argparse
from pathlib import Path
import corsair
from . import utils

__all__ = ['main']


class ArgumentParser(argparse.ArgumentParser):
    """Inherit ArgumentParser to override the behaviour of error method."""
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, '\n%s: error: %s\n' % (self.prog, message))


def parse_arguments():
    """Parse and validate arguments."""

    parser = ArgumentParser(prog=corsair.__title__,
                            description=corsair.__description__)
    parser.add_argument('-v', '--version',
                        action='version',
                        version='%(prog)s v' + corsair.__version__)
    parser.add_argument('-r', '--regmap',
                        metavar='file',
                        dest='regmap',
                        help='read register map from input file')
    parser.add_argument('-c', '--config',
                        metavar='file',
                        dest='config',
                        help='read configuration from file')
    parser.add_argument('--template-regmap',
                        metavar='file',
                        dest='template_regmap',
                        help='create register map template file')
    parser.add_argument('--template-config',
                        metavar='file',
                        dest='template_config',
                        help='create configuration template file')
    parser.add_argument('--dump-regmap',
                        metavar='file',
                        dest='dump_regmap',
                        help='dump register map to file')
    parser.add_argument('--dump-config',
                        metavar='file',
                        dest='dump_config',
                        help='dump configuration to file')
    parser.add_argument('--hdl',
                        dest='hdl',
                        action='store_true',
                        help='create HDL module with register map')
    parser.add_argument('--lb-bridge',
                        dest='lb_bridge',
                        action='store_true',
                        help='create HDL module with bridge to LocalBus')
    parser.add_argument('--docs',
                        dest='docs',
                        action='store_true',
                        help='create docs for register map')

    # check if no arguments provided
    if len(sys.argv) == 1:
        parser.parse_args(['--help'])
        # argparse will raise SystemExit here

    # get arguments namespace
    args = parser.parse_args()

    # check conflicts
    if not args.regmap and (args.hdl or args.docs):
        parser.error("Not able to proceed without -r/--regmap argument!")

    if args.lb_bridge and not (args.regmap or args.config):
        parser.error("Not able to proceed without -r/--regmap or -c/--config argument!")

    if not args.regmap and args.dump_regmap:
        parser.error("Not able to proceed without -r/--regmap argument!")

    if args.dump_config and not (args.regmap or args.config):
        parser.error("Not able to proceed without -r/--regmap or -c/--config argument!")

    return args


def main():
    """Program main."""
    # parse arguments
    args = parse_arguments()

    # create templates
    if args.template_regmap:
        regs = [corsair.Register('spam', 'Register spam', 0),
                corsair.Register('eggs', 'Register eggs', 4)]
        regs[0].add_bfields([
            corsair.BitField('foo', 'Bit field foo', lsb=0, width=7, access='rw', initial=42),
            corsair.BitField('bar', 'Bit field bar', lsb=24, width=1, access='wo', modifiers=['self_clear'])
        ])
        regs[1].add_bfields(corsair.BitField('baz', 'Bit field baz', lsb=16, width=16, access='ro'))
        rmap = corsair.RegisterMap()
        rmap.add_regs(regs)
        corsair.RegisterMapWriter()(args.template_regmap, rmap)

    if args.template_config:
        config = corsair.Configuration()
        corsair.ConfigurationWriter()(args.template_config, config)

    # parse input files
    if args.config:
        config = corsair.ConfigurationReader()(args.config)
    else:
        config = corsair.Configuration()

    if args.regmap:
        rmap = corsair.RegisterMapReader()(args.regmap, config)
    else:
        rmap = corsair.RegisterMap(config)

    # dump files
    if args.dump_regmap:
        corsair.RegisterMapWriter()(args.dump_regmap, rmap)

    if args.dump_config:
        corsair.ConfigurationWriter()(args.dump_config, rmap.config)

    # prepare for artifacts generation
    if args.regmap:
        outdir = Path(args.regmap).parent
    elif args.config:
        outdir = Path(args.config).parent
    if 'name' in config.names:
        outname = config['name'].value
    else:
        outname = Path(args.regmap).stem

    # create register map HDL
    if args.hdl:
        pass

    # create bridge to LocalBus HDL
    if args.lb_bridge:
        if config['lb_bridge']['type'].value == 'none':
            print("Local Bus bridge type is 'none' - no need to generate any file.")
        else:
            lb_bridge_name = '%s2lb_%s.v' % (config['lb_bridge']['type'].value, outname)
            lb_bridge_path = str(outdir / lb_bridge_name)
        corsair.LbBridgeWriter()(lb_bridge_path, config)

    # create docs
    if args.docs:
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
