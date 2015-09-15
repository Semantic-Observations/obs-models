""" annotate.py
    Bryce Mecum (mecum@nceas.ucsb.edu)

    Overview:

    At Startup:
        - Create blank graph
        - Load annotation mappings
        - Load the dataset to be annotated

    Workflow:
        - For each mapping,
            - Grab the data about that mapping
            - Grab the annotations for each mapping.
            - Generate the triples needed.



    Triples to define...

        Each observation
            type: OBOE:Observation
            oboe:ofEntity
            hasMeasurement
        For each measuremnet
            type: oboe:Measurement
            oboe:hasValue
            oboe:ofCharacteristic
            oboe:standard
        For each characteristic
            type: oboe:characteristic
"""


import RDF
import pandas
import csv


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


def addTriple(model, s, o, p):
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

    statement = RDF.Statement(s_node, p_node, o_node)

    if statement is None:
        raise Exception("new RDF.Statement failed")

    model.add_statement(statement)


def addObservation(model, ns, observation):
    """
        Adds `observation` (and related triples) to the graph.
    """

    observation_id = observation.attrib.get("id")
    observation_node = RDF.Node(blank=observation_id)

    print "Adding triples for observation with id:'%s' to the graph." % observation_id
    addTriple(model, observation_node, RDF.Uri(ns["rdf"]+"type"), RDF.Uri(ns["oboe"]+"Observation"))


def addMeasurement(model, ns, measurement):
    """
        Adds `measurement` (and related triples) to the graph.
    """

    measurement_id = measurement.attrib.get("id")
    measurement_node = RDF.Node(blank=measurement_id)

    print "Adding triples for measurement with id:'%s' to the graph." % measurement_id
    addTriple(model, measurement_node, RDF.Uri(ns["rdf"]+"type"), RDF.Uri(ns["oboe"]+"Measurement"))

    # characteristic
    # standard


def addEntity(model, ns, entity):
    """
        Adds `entity` (and related triples) to the graph.
    """

    entity_id = entity.attrib.get("id")
    entity_node = RDF.Node(blank=entity_id)

    print "Adding triples for entity with id:'%s' to the graph." % entity_id
    addTriple(model, entity_node, RDF.Uri(ns["rdf"]+"type"), RDF.Uri(ns["oboe"]+"Entity"))


def processMapping(mapping, data):
    """
    """

    attribute = mapping.attrib.get("attribute")
    measurement = mapping.attrib.get("measurement")
    value = mapping.attrib.get("value")
    condition = mapping.attrib.get("if")

    # Check if we have a valid mapping
    if all([attribute, measurement]) is None:
        print "Invalid mapping statement. Mapping statements need at least"\
        " an attribute and a measurement to map to."

    # Validate the mapping
    #   - Column names should be present

    if condition is not None:
        processed_condition = processMappingCondition(condition)




    return mapping


def processMappingCondition(condition):
    """
        Process the text of the mapping condition of a mapping. The general form
        will be "<attribute> <eq:lt:gt> <value>".
    """

    tokens = condition.split(" ")

    if len(tokens) != 3:
        print "Mapping condition '%s' is in an invalid form." % condition

        return []

    return tokens


def loadAnnotations(filename):
    """
        Load observation annotations from `filename`.
    """

    namespaces = {}
    observations = {}
    measurements = {}
    entities = {}
    mappings = {}

    with open(filename, "rbU") as f:
        reader = csv.reader(f)

        line = reader.next();
        print line
        more = True

        while more:
            
        return



        state = None

        # for row in reader:
        #     if row[0] is '':
        #         state = None
        #
        #     if state is None:
        #         header = row[0]
        #
        #         print "header is `%s`" % header
        #
        #         if header == "NAMESPACES":
        #             print "found namespaces"
        #             state = "ns"
        #         elif header == "ALIGNMENTS":
        #             print "align"
        #             state = "align"
        #         elif header == "OBSERVATIONS":
        #             print "obs"
        #             state = "obs"
        #         elif header == "MAPPINGS":
        #             print "mappings"
        #             state = "map"
        #     else:
        #         if state is "ns":
        #             # Add the namespace
        #             namespaces[row[0]] = row[1]
        #         elif state is "align":
        #             # Add triples for the alignement
        #             # TODO
        #         elif state is "obs":
        #             pass
        #         elif state is "map":
        #             pass
        #     print state

    print namespaces


def loadDataset(filename):
    """
        Load dataset to be annotated from `filename`.
    """

    dataset = pandas.read_csv(filename)

    # Debug
    print "dataset.head()..."
    print dataset.head()

    return dataset


def main():
    model = createModel()

    ns = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "oboe": "http://ecoinformatics.org/oboe/oboe.1.0/oboe-core.owl#"
    }

    annotations = loadAnnotations("annotations.csv")
    dataset = loadDataset("SargassoSeaLipids-X1103_CTD_profiles.flat9.txt")

    return

    for entity in entities:
        addEntity(model, ns, entity)

    for observation in observations:
        measurement = observation.find("./measurement")

        if measurement is not None:
            addMeasurement(model, ns, measurement)

        addObservation(model, ns, observation)

    for mapping in mappings:
        processMapping(mapping, dataset)

    serializeModel(model, ns, "data.ttl")

if __name__ == "__main__":
    main()
