""" annotate.py
    Bryce Mecum (mecum@nceas.ucsb.edu)

    Overview:

    At Startup:
        - Create blank graph
        - Load the dataset to be annotated
        - Load and process annotation mappings
"""


import RDF
import pandas
import csv
import re


class Annotation:
    """
        Class to hold the information about the annotation process.
        This is passed around from function to function.
    """

    def __init__(self, model, dataset):
        self.model = model # An RDF Model
        self.dataset = dataset # A pandas data_frame

        # Characteristics of the annotation template
        self.meta = {}
        self.namespaces = {}
        self.triples = []
        self.observations = {}
        self.measurements = {}
        self.entities = {}
        self.mappings = {}


    def __str__(self):
        """ Pretty-printing method for the annotation."""

        outstring = ""

        if len(self.meta) > 0:
            outstring += "META\n"

            for m in self.meta:
                outstring += "  %s: %s\n" % (m, self.meta[m])

        if len(self.namespaces) > 0:
            outstring += "NAMESPACES\n"

            for n in self.namespaces:
                outstring += "  %s: %s\n" % (n, self.namespaces[n])

        if len(self.triples) > 0:
            outstring += "TRIPLES\n"

            for t in self.triples:
                outstring += "  %s %s %s\n" % t

        if len(self.observations) > 0:
            outstring += "OBSERVATIONS\n"

            for o in self.observations:
                outstring += "  %s\n" % o

        if len(self.measurements) > 0:
            outstring += "MEASUREMENTS\n"

            for m in self.measurements:
                outstring += "  %s\n" % m

        if len(self.entities) > 0:
            outstring += "ENTITIES\n"

            for e in self.entities:
                outstring += "  %s\n" % e

        if len(self.mappings) > 0:
            outstring += "MAPPINGS\n"

            for m in self.mappings:
                outstring += "  %s\n" % n

        return outstring


def addAnnotationMeta(annotation, row):
    """ Add the annotation metadata from `row` to `annotation`."""

    annotation.meta[row[0]] = row[1]


def addAnnotationNamespaces(annotation, row):
    """ Add the annotation namespaces from `row` to `annotation`."""

    annotation.namespaces[row[0]] = row[1]


def addAnnotationTriples(annotation, row):
    """ Add the annotation triples from `row` to `annotation`."""

    annotation.triples.append((row[0], row[1], row[2]))


def addAnnotationObservation(annotation, row):
    """ Add the OBOE:Observation in `row` to `annotation`."""

    blank_node = RDF.Node(blank=row[1])

    # Save the bnode
    annotation.observations[row[1]] = blank_node

    # Add the triple
    addStatement(annotation.model,
                 blank_node,
                 RDF.Uri(annotation.namespaces["rdf"]+"type"),
                 RDF.Uri(annotation.namespaces["oboe"]+"Observation"))

    addStatement(annotation.model,
                 blank_node,
                 RDF.Uri(annotation.namespaces["rdf"]+"label"),
                 row[1])


def addAnnotationEntity(annotation, row, parent):
    """ Add the OBOE:Entity in `row` to `annotation`."""

    blank_node = RDF.Node(blank=row[2])

    # rdf:type
    addStatement(annotation.model,
                 blank_node,
                 RDF.Uri(annotation.namespaces["rdf"]+"type"),
                 RDF.Uri(annotation.namespaces["oboe"]+"Entity"))

    # oboe:ofEntity
    addStatement(annotation.model,
                 annotation.observations[parent],
                 RDF.Uri(annotation.namespaces["oboe"]+"ofEntity"),
                 blank_node)
    # rdf:label
    addStatement(annotation.model,
                 blank_node,
                 RDF.Uri(annotation.namespaces["rdf"]+"label"),
                 row[2])


def addAnnotationMeasurementTemplate(annotation, row, parent):
    """  Add the template for an OBOE:Measurement in `row` to `annotation`."""

    annotation.measurements[row[2]] = {
        'observation': parent
    }


def addAnnotationContext(annotation, row, parent):
    """  Add the OBOE:hasContext statement in `row` to `annotation`."""


def addAnnotationValues(annotation, key, values):
    """ Adds `values` as OBOE:Measurements to the graph."""

    for value in values:
        if key not in annotation.measurements:
            print "Measurement '%s' not found. Moving to next row." % key
            continue

        addAnnotationValue(annotation, key, value)


def addAnnotationValue(annotation, key, value):
    """ Adds `value` as OBOE:Measurements to the graph."""

    template = annotation.measurements[key]

    if 'observation' not in template:
        print "Measurement template doesn't reference an observation. Skipping."
        return

    observation_node = annotation.observations[template['observation']]
    measurement_node = RDF.Node(blank="")

    # rdf:type
    addStatement(annotation.model,
                 measurement_node,
                 annotation.namespaces["rdf"]+"type",
                 RDF.Uri(annotation.namespaces["oboe"]+"Measurement"))

    # oboe:Measurement oboe:hasValue
    addStatement(annotation.model,
                 measurement_node,
                 annotation.namespaces["oboe"]+"hasValue",
                 str(value))

    # oboe:Observation oboe:hasMeasurement
    addStatement(annotation.model,
                 observation_node,
                 annotation.namespaces["oboe"]+"hasMeasurement",
                 measurement_node)


def createModel():
    """
        Creates an in-memory RDF store using redland.
        Adapted from previous work by mbjones.
    """

    storage = RDF.Storage(storage_name="hashes",
                          name="autoannotate",
                          options_string="new='yes',hash-type='memory',dir='.'")

    if storage is None:
        raise Exception("new RDF.Storage failed")

    model=RDF.Model(storage)

    if model is None:
        raise Exception("new RDF.model failed")

    return model


def serializeModel(model, ns, filename, format=None):
    """
        Serializes `model` to disk at `filename` in `format`.
        Adapted from previous work by mbjones.
    """

    if format == None:
        format = "turtle"

    serializer=RDF.Serializer(name=format)

    for prefix in ns:
        serializer.set_namespace(prefix, RDF.Uri(ns[prefix]))

    serializer.serialize_model_to_file(filename, model)


def addStatement(model, s, p, o):
    """
        Adds the triple (s, o, p) to the model (model).

        Performs pre-checking on inputs to make sure triples are added to the
        graph in the correct form.

        Adapted from previous work by mbjones
    """

    # Assume subject is a URI string if it is not an RDF.Node
    if (type(s) is not RDF.Node):
        s_node = RDF.Uri(s)
    else:
        s_node = s
    # Assume predicate is a URI string if it is not an RDF.Node
    if (type(p) is not RDF.Node):
        p_node = RDF.Uri(p)
    else:
        p_node = p
    # Assume object is a literal if it is not an RDF.Node
    if (type(o) is not RDF.Node):
        o_node = RDF.Node(o)
    else:
        o_node = o

    statement=RDF.Statement(s_node, p_node, o_node)

    if statement is None:
        raise Exception("new RDF.Statement failed")

    model.add_statement(statement)


def loadAnnotations(filename, annotation):
    """
        Load observation annotations from `filename`.
    """

    with open(filename, "rbU") as f:
        reader = csv.reader(f)


        """ Keep track of what state we're in.

            States refer to the header groupings in the annotations file.
            When we are in a state (not at a blank line or an all-caps header),
            we do the appropriate work for that state.
        """
        state = None


        """ `stack` is used to keep track of the annotation hierarchy in the
            following recursive-descent parser. We do this because some
            concepts need to know their parent in order to generate triples
            in the parent's node. For example, OBOE:Measurements need to know
            which OBOE:Observation they belong to (with OBOE:hasMeasurement).

            This is my way of keeping track of that hierarchy.
        """

        stack = []


        for row in reader:
            # Skip any blank lines
            if len(''.join(row).strip()) == 0:
                continue

            # Get the first value in the row to test if it's a header
            header = row[0]

            # Test if it's a heading for a group
            if re.match("[A-Z]+", header):
                if header == "META":
                    state = "META"
                elif header == "NAMESPACES":
                    state = "NAMESPACES"
                elif header == "TRIPLES":
                    state = "TRIPLES"
                elif header == "OBSERVATIONS":
                    state = "OBSERVATIONS"
                elif header == "MAPPINGS":
                    state = "MAPPINGS"
            else:
                # We aren't at a a header so we need to do actual work

                if state == "META":
                    addAnnotationMeta(annotation, row)

                elif state == "NAMESPACES":
                    addAnnotationNamespaces(annotation, row)

                elif state == "TRIPLES":
                    addAnnotationTriples(annotation, row)

                elif state == "OBSERVATIONS":
                    # Manage the stack
                    for i in range(len(row)):
                        if len(row[i].strip()) > 0:
                            # Adjust the stack
                            depth = i+1

                            if depth > len(stack):
                                stack.append((row[i], row[i+1]))

                            elif depth == len(stack):
                                stack.pop()
                                stack.append((row[i], row[i+1]))

                            elif depth < len(stack):
                                for j in range(len(stack) - depth + 1):
                                    stack.pop()

                                stack.append((row[i], row[i+1]))
                            break

                    # DEBUG: Print the stack
                    # indent = 1
                    # for n in stack:
                    #     outstring = ""
                    #     for i in range(indent):
                    #         outstring += "  "
                    #     outstring += "(%s, %s)" % (n[0], n[1])
                    #     print outstring
                    #     indent += 1
                    #/Debug

                    # Observations are at indent 1
                    if len(stack) == 1:
                        addAnnotationObservation(annotation, row)
                    # Measurements/Entities/etc are at indent 2
                    elif len(stack) == 2:
                        parent = stack[0][1]
                        node_type = row[1]

                        if node_type == "entity":
                            addAnnotationEntity(annotation, row, parent)
                        elif node_type == "measurement":
                            addAnnotationMeasurementTemplate(annotation, row, parent)
                        elif node_type == "context":
                            addAnnotationContext(annotation, row, parent)

                elif state == "MAPPINGS":
                    # Each mapping is at least an attribute/key pair.
                    attrib = row[0]
                    key = row[1]

                    dataset = annotation.dataset

                    if attrib not in dataset:
                        print "Couldn't find attribute %s in dataset with columns %s. Moving to next row." % (attrib, dataset.columns)
                        continue

                    # Do straight mapping for straight mappings
                    if len(''.join(row[2:]).strip()) == 0:
                        matched_data = dataset[attrib]

                    # Otherwise, do conditional mapping
                    else:
                        # Find the mapping condition (lt, gt, etc)
                        condition = row[3].split(" ")

                        if len(condition) != 3:
                            print "Condition format error. Expected three tokens, separated by a space. Moving to next row."
                            continue

                        if condition[1] == "eq":
                            matched_data = dataset[attrib][dataset[attrib] == int(condition[2])]
                        elif condition[1] == "neq":
                            matched_data = dataset[attrib][dataset[attrib] != int(condition[2])]
                        elif condition[1] == "lt":
                            matched_data = dataset[attrib][dataset[attrib] < int(condition[2])]
                        elif condition[1] == "gt":
                            matched_data = dataset[attrib][dataset[attrib] > int(condition[2])]
                        elif condition[1] == "lte":
                            matched_data = dataset[attrib][dataset[attrib] >= int(condition[2])]
                        elif condition[1] == "gte":
                            matched_data = dataset[attrib][dataset[attrib] <= int(condition[2])]
                        else:
                            print "Unrecognized comparison operator. Try one of eq|neq|lt|gt|lte|gte. Moving to next row."

                    addAnnotationValues(annotation, key, matched_data[0:5])


def loadDataset(filename):
    """
        Load dataset to be annotated from `filename`.
    """

    dataset = pandas.read_fwf(filename)

    # Debug
    # print "dataset.head()..."
    # print dataset.head()
    # /Debug
    return dataset


def main():
    model = createModel()
    dataset = loadDataset("SargassoSeaLipids-X1103_CTD_profiles.flat9.txt")

    annotation = Annotation(model, dataset)
    annotations = loadAnnotations("sargasso-annotations.csv", annotation)

    # print annotation

    serializeModel(annotation.model, annotation.namespaces, "sargasso.ttl")

if __name__ == "__main__":
    main()
