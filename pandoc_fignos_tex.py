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


def find_ref_str(value, pattern_ref, num_ref):
    if isinstance(value, dict):
        if 't' in value and 'c' in value:
            if value['t'] == 'Str':
                sys.stderr.write('find_ref_str: %s -> %s\n' % (value['c'], str(value['t'])))
                numbered_ref = '%d' % num_ref
                value['c'] = numbered_ref.decode("utf-8")
                return(value)
            else:
                find_ref_str(value['c'], pattern_ref, num_ref)
    elif isinstance(value, list):
        for v in value:
            find_ref_str(v, pattern_ref, num_ref)


def replace_fig_references(key, value, fmt, meta):
    global num_refs  # Global references counter
    global references
    # sys.stderr.write('Key: %s -> %s\n' % (key, Str(value)))
    if key in ['Para', 'Plain'] and fmt == "docx":        
        for i, x in enumerate(value):
            if re.match(r'.*ref.*', str(x).replace('\n', ' ')):
                for r in references.keys():
                    # sys.stderr.write('LOOKING FOR: %s -> %s\n' % (r, Str(x)))
                    pattern_ref = re.compile('.*%s.*' % r)
                    if re.match(pattern_ref, str(x).replace('\n', ' ')):
                        find_ref_str(x, pattern_ref, references[r])
                        value[i] = x
        return Para(value)


def replace_fig_label(value, label_num):
    # sys.stderr.write('REPLACE_IMG_LABEL: %s\n' % str(value))
    if isinstance(value, dict):
        if 't' in value and 'c' in value:
            if value['t'] == 'Str':
                sys.stderr.write('replace_fig_label: %s -> %s\n' % (value['c'], str(value['t'])))
                numbered_ref = 'Figure %d. ' % label_num
                value['c'] = numbered_ref.decode("utf-8")
                return(value)
            else:
                replace_fig_label(value['c'], label_num)
    elif isinstance(value, list):
        for v in value:
            replace_fig_label(v, label_num)


# pylint: disable=unused-argument,too-many-branches
def process_figs(key, value, fmt, meta):
    # pylint: disable=global-statement
    global num_refs  # Global references counter
    global references
    if fmt == "docx" and key == "Image":
        # sys.stderr.write('KEY: %s, VALUE: %s\n' % (key, value))
        for i, x in enumerate(value):
            if re.match(r'.*label.*', str(x).replace('\n', ' ')):
                num_refs += 1
                m = re.match(r".*label.*\'(.*?)\'\]",
                             str(x[0]).replace('\n', ' '))
                label = m.group(1)
                references[label] = num_refs
                replace_fig_label(x[0], num_refs)
                value[i] = x
        return Image(*value)

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
    # Second pass
    altered = functools.reduce(lambda x, action: walk(x, action, fmt, meta),
                               [replace_fig_references], altered)

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
