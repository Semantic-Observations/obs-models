""" annotate.py
    Bryce Mecum (mecum@nceas.ucsb.edu)

    This script creates an annotation object which takes as input an
    annotation template which is a CSV file.

    To run the script, call it with at least a path to an annotation template.

        `python annotate.py mytemplate.csv`

    Optionally, specify a number of rows and/or an output filename:

        `python annotate.py -n 5 mytemplate.csv` # First five rows
        `python annotate.py -n 5 -o out.ttl mytemplate.csv` # Writes to out.ttl
"""

import sys
import pandas
import csv
import re
import argparse

from csvtotriples import annotation


if __name__ == "__main__":
    # Parse command line args
    parser = argparse.ArgumentParser(description='Generate an RDF graph from a CSV template.')
    parser.add_argument("-n", type=int, help="Number of rows to add to the graph. Default: All rows.")
    parser.add_argument("-o", help="Filename to store the resulting RDF graph. Default: `filename`.ttl")
    parser.add_argument("filename", help="Path to an annotation template (.csv).")

    args = parser.parse_args()

    # Createa and run the annotation
    anno = annotation.Annotation(args.filename, nrows=args.n)
    anno.parse()
    anno.process()

    # Handle output filename
    if args.o is None:
        outfile = args.filename.replace(".csv", ".ttl")
    else:
        outfile = args.o

    anno.serialize(outfile)

    # Print model size
    print anno
