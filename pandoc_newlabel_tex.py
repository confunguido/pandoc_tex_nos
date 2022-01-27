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
supp_enabled = False
supp_str = ''
aux_dict = dict()
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
                numbered_ref = '%s' % num_ref
                ##value['c'] = numbered_ref.decode("utf-8")
                sys.stderr.write('find_ref_str: %s -> %s\n' % (value['c'], str(numbered_ref)))
                value['c'] = numbered_ref
                return(value)
            else:
                find_ref_str(value['c'], pattern_ref, num_ref)
    elif isinstance(value, list):
        for v in value:
            find_ref_str(v, pattern_ref, num_ref)

def replace_newlabel_references(key, value, fmt, meta):
    global aux_dict
    if key in ['Para', 'Plain'] and fmt == "docx":
    #if fmt == "docx": 
        for i, x in enumerate(value):
            if re.match(r'.*reference-type.*', str(x).replace('\n', ' ')):
                ##sys.stderr.write('Key: %s -> %s\n' % (key, Str(value)))
                for r in aux_dict.keys():
                    ##sys.stderr.write('LOOKING FOR: %s -> %s\n' % (r, Str(x)))
                    pattern_ref = re.compile('.*?\'%s\'.*?' % r)
                    if re.match(pattern_ref, str(x).replace('\n', ' ')):
                        sys.stderr.write('FOUND: %s -> %s\nMoving to find ref str\n' % (r, Str(x)))
                        find_ref_str(x, pattern_ref, aux_dict[r])
                        value[i] = x
        return Para(value)

# Main routine ---------------------------------------------------


def main():
    """Filters the document AST."""
    # pylint: disable=global-statement
    global PANDOCVERSION
    global AttrMath
    global aux_dict
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

    if not ('aux' in meta):
        quit()
    
    sys.stderr.write(json.dumps(meta['aux']))
    aux_file = open(meta['aux']['c'],'r')
    aux_data = aux_file.readlines()
    for aa in aux_data:
        match = re.search(r'^\\newlabel\{(.*?)\}\{\{(.*?)\}', aa)
        if match :        
            aux_dict[match.group(1)] = match.group(2)
    for kk in aux_dict.keys():
        sys.stderr.write('%s -> %s\n'%(kk, aux_dict[kk]))

    ## sys.stderr.write(json.dumps(blocks))

    # First pass
    attach_attrs_math = attach_attrs_factory(Math, allow_space=True)
    detach_attrs_math = detach_attrs_factory(Math)
    insert_secnos = insert_secnos_factory(Math)
    delete_secnos = delete_secnos_factory(Math)
    altered = functools.reduce(lambda x, action: walk(x, action, fmt, meta),
                               [attach_attrs_math, insert_secnos,
                                replace_newlabel_references, delete_secnos,
                                detach_attrs_math], blocks)
    # Second pass
    # altered = functools.reduce(lambda x, action: walk(x, action, fmt, meta),
    #                            [replace_newlabel_references], altered)

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
