""" skeleton.py

    Generate an OBOE annotation template skeleton from a dataset.
"""

import sys
import re
import pandas
import csv


def main():
    # Open file with Pandas
    if len(sys.argv) != 2:
        print "Unexpected number of command line arguments. Expected `python skeleton.py some_dataset.csv`"
        sys.exit()

    filename = sys.argv[1]

    """ Extract the column names
        First, check if the file is *.csv
        Use pandas.read_csv because I'm sure pandas is less error-prone

        Otherwise, detect it from what's inside the first line of the file.
    """

    if re.search("\A.+\.csv\Z", filename):
        dataset = pandas.read_csv(filename)

        columns = dataset.columns.tolist()
    else:
        with open(filename, "rb") as f:
            header_line = f.readline()

            """ Autodetect file format using these rules:

                CSV: Has commas
                TSV: Has tabs
                FWF: Has neither
            """

            # CSV
            if len(header_line.split(",")) > 1:     #CSV
                print "Reading in dataset as CSV."
                dataset = pandas.read_fwf(filename)
            elif len(header_line.split("\t")) > 1:  # TSV
                print "Reading in dataset as TSV."
                dataset = pandas.read_table(filename)
            else:
                print "Reading in dataset as FWF."
                dataset = pandas.read_fwf(filename) #FWF

            columns = dataset.columns.tolist()

    # Do work for each column
    outfilename = "skeleton-%s.csv" % filename
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)

        for header in ['META', 'NAMESPACES', 'TRIPLES']:
            writer.writerow([header])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])


        # Observations
        writer.writerow(['OBSERVATIONS'])
        writer.writerow([])


        index = 1
        for column in columns:
            writer.writerow(['#'+column])
            writer.writerow(['observation', 'o'+str(index)])
            writer.writerow(['', 'entity', 'e'+str(index), 'foo:EditMe'])
            writer.writerow(['', 'measurement', 'm'+str(index)])
            writer.writerow(['', '', 'characteristic', 'foo:EditMe'])
            writer.writerow(['', '', 'standard', 'foo:EditMe'])
            writer.writerow(['', '', 'datatype', 'foo:EditMe'])

            writer.writerow([])
            index += 1

        writer.writerow([])
        writer.writerow([])
        writer.writerow([])


        # Mappings
        writer.writerow(['MAPPINGS'])

        index = 1
        for column in columns:
            writer.writerow([column, 'm'+str(index)])
            index += 1


        # Datatypes
        writer.writerow(['DATATYPES'])

        index = 1
        for column in columns:
            writer.writerow([column, 'm'+str(index)])
            index += 1

    print "Created template at `%s`." % outfilename


if __name__ == "__main__":
    main()
