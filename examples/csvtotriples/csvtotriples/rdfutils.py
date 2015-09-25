""" rdfutils.py

    Various functions that help in working with RDF graphs usingn the
    Redland's bindings.
"""

import RDF


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
