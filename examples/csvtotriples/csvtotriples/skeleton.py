""" skeleton.py

    Generate an OBOE annotation skeleton from a dataset.
"""

import pandas
import csv


def main():
    # Open file with Pandas
    # TODO
    columns = ['test', 'this', 'out']


    # Do work for each column
    with open("skeleton.csv", "wb") as f:
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


if __name__ == "__main__":
    main()
