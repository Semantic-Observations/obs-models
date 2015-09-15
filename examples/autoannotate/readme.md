# Auto Annotate

This folder contains the working materials to automatically annotate a dataset
with semantic annotations from an observation ontology. This work can be done by
hand but is tedious and time-consuming for larger datasets.

This script (`annotate.py`) reads in semantic annotations from an CSV file and produces and
semantic observations graph for the data inside a CSV file.

## Annotations File

The annotations file format was designed to make it easy for the user to describe their annotations for the dataset.

The file contains five headers which contain specific information relevant to the automatic annotation process:

- META: Identifiers for the metadata and data
- NAMESPACES: Namespaces for the annotation graph
- TRIPLES: Any triples the user wants to manually specify
- OBSERVATIONS: The observations the data are being annotated with
- MAPPINGS: The mappings between observations and data