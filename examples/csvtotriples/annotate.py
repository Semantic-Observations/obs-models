""" annotate.py
    Bryce Mecum (mecum@nceas.ucsb.edu)

    This script creates an annotation object which takes as input an
    annotation template which is a CSV file.

    The annotation object's annotation method reads the annotation template.

    The annotation object's serialize method writes the collected set of
    triples to disk in the specified format.
"""

import pandas
import csv
import re

from csvtotriples import annotation


if __name__ == "__main__":
    anno = annotation.Annotation("sargasso-annotations.csv")
    anno.process()
    anno.serialize("sargasso.ttl")
