""" annotate.py
    Bryce Mecum (mecum@nceas.ucsb.edu)

    This script creates an annotation object which takes as input an
    annotation template which is a CSV file.

    The annotation object's annotation method reads the annotation template.

    The annotation object's serialize method writes the collected set of
    triples to disk in the specified format.
"""

import sys
import pandas
import csv
import re

from csvtotriples import annotation


if __name__ == "__main__":
    # Parse command line args to get filename
    if len(sys.argv) != 2:
        print "Unexpected number of command line arguments. Expected `python annotate.py your_template.csv`"
        sys.exit()

    filename = sys.argv[1]

    anno = annotation.Annotation(filename)
    anno.parse()
    anno.process()
    anno.serialize(filename + ".ttl")

    print anno
