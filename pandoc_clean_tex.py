# Definitions ---------------------------------------
import re
import functools
import argparse
import json
# import uuid
import sys

from pandocfilters import walk
from pandocfilters import Math, RawInline, Str, Span, Para, Image

import pandocxnos
# from pandocxnos import PandocAttributes
from pandocxnos import STRTYPES, STDIN, STDOUT
from pandocxnos import check_bool, get_meta
from pandocxnos import attach_attrs_factory, detach_attrs_factory
from pandocxnos import insert_secnos_factory, delete_secnos_factory
from pandocxnos import elt

# from pandocxnos import repair_refs, process_refs_factory, replace_refs_factory
__version__ = '1.0'

# Read the command-line arguments ------------------------------------
parser = argparse.ArgumentParser(description='Pandoc equations numbers filter.')
parser.add_argument('--version', action='version',
                    version='%(prog)s {version}'.format(version=__version__))
parser.add_argument('fmt')
parser.add_argument('--pandocversion', help='The pandoc version.')
args = parser.parse_args()


# Variables -----------------------------------------------------------
num_refs = 0
references = {}

# Variables for tracking section numbers
numbersections = False

PANDOCVERSION = None
AttrMath = None

# Functions ---------------------------------------------------

def replace_fig_label(value):
    # sys.stderr.write('REPLACE_REVIEW_LABEL: %s\n' % str(value))
    if isinstance(value, dict):
        if 't' in value and 'c' in value:
            if value['t'] == 'Str':
                sys.stderr.write('replace_REVIEW_label: %s -> %s\n' % (value['c'], str(value['t'])))
                value['c'] = ''
                return(value)
            else:
                replace_fig_label(value['c'])
    elif isinstance(value, list):
        for v in value:
            replace_fig_label(v)


# pylint: disable=unused-argument,too-many-branches
def process_figs(key, value, fmt, meta):
    # pylint: disable=global-statement
    global num_refs  # Global references counter
    global references
    if fmt == "docx" and key == "Para":
        for i, x in enumerate(value):
            if re.match(r'.*label.*', str(x).replace('\n', ' ')):
                # sys.stderr.write('KEY: %s, VALUE[%d]: %s, X: %s\n' % (key, i,value[i], x))
                m = re.match(r".*label.*\'(.*?R.*?Com.*?)\'\]",
                             str(x).replace('\n', ' '))
                if m:
                    # label = m.group(1)
                    # sys.stderr.write('Label[%d] = %s\n' % (i,label))
                    replace_fig_label(x)
                    value[i] = x
        return Para(value)

# Main routine ---------------------------------------------------


def main():
    """Filters the document AST."""
    # pylint: disable=global-statement
    global PANDOCVERSION
    global AttrMath

    # Get the output format and document
    fmt = args.fmt
    doc = json.loads(STDIN.read())

    # Initialize pandocxnos
    # pylint: disable=too-many-function-args
    PANDOCVERSION = pandocxnos.init(args.pandocversion, doc)

    # Element primitives
    AttrMath = elt('Math', 2)

    # Chop up the doc
    meta = doc['meta'] if PANDOCVERSION >= '1.18' else doc[0]['unMeta']
    blocks = doc['blocks'] if PANDOCVERSION >= '1.18' else doc[1:]

    # First pass
    attach_attrs_math = attach_attrs_factory(Math, allow_space=True)
    detach_attrs_math = detach_attrs_factory(Math)
    insert_secnos = insert_secnos_factory(Math)
    delete_secnos = delete_secnos_factory(Math)
    altered = functools.reduce(lambda x, action: walk(x, action, fmt, meta),
                               [attach_attrs_math, insert_secnos,
                                process_figs, delete_secnos,
                                detach_attrs_math], blocks)

    # Update the doc
    if PANDOCVERSION >= '1.18':
        doc['blocks'] = altered
    else:
        doc = doc[:1] + altered

    # Dump the results
    json.dump(doc, STDOUT)

    # Flush stdout
    STDOUT.flush()

if __name__ == '__main__':
    main()
