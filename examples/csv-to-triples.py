#!/opt/local/bin/python
#
# A script to read RDF subject/triple/object properties form a csv file and turn them into RDF models.
# The CSV file expects an initial section with Namespaces and then a second section with triples
# with a column each for Subject, Predicate, and Object values.  Any value which contains a colon ":"
# will be interpreted as either a prefix:concept pair used to construct a URI, or as a blank node if the
# prefix is an underscore ("_") character.  Any other values will be treated as literals, including any strings
# for which the prefix does not match a prefix in the namespace dictionary.
#
# Matt Jones and Adam Shepherd

def add_statements_from_csv(filename, model, ns):

    cfile  = open(filename, "rb")
    reader = csv.reader(cfile)

    triple_section = False
    ns_section = False
    rownum = 0w
    for row in reader:
        rownum = rownum+1
        print("Processing row: " + str(rownum))
        if row[0].strip() == '':
            continue        # Skip blank rows
        elif row[0] == 'Subject':
            header = row
            triple_section = True
            ns_section = False
        elif row[0] == 'Namespaces':
            ns_section = True
        elif ns_section:
            prefix = row[0]
            nsuri = row[1]
            if (prefix not in ns):
                ns[prefix] = nsuri
        elif triple_section:
            subject = row[0]
            predicate = row[1]
            object = row[2]
            print("Constructing: " + subject + " " + predicate + " " + object)

            # Parse the value to determine if it is a blank node or a prefix:class, then turn them into proper nodes
            s_node = cell_to_node(subject, ns)
            print("Subject B/R/L: " + str(s_node.is_blank()) + "/" + str(s_node.is_resource()) + "/" + str(s_node.is_literal()))
            p_node = cell_to_node(predicate, ns)
            print("Predicate B/R/L: " + str(p_node.is_blank()) + "/" + str(p_node.is_resource()) + "/" + str(p_node.is_literal()))
            o_node = cell_to_node(object, ns)
            print("Object B/R/L: " + str(o_node.is_blank()) + "/" + str(o_node.is_resource()) + "/" + str(o_node.is_literal()))

            # add a Statement to the model with the s, p, o
            addStatement(model, s_node, p_node, o_node)
            model.sync()

    cfile.close()

def cell_to_node(cell, ns):

    newnode = None

    # split out the prefix
    tokens = str.split(cell, ":")
    if (len(tokens) > 1):
        prefix = tokens[0]
        concept = tokens[1]

        # If prefix == "_" then make a blank node
        if (prefix=="_"):
            newnode = RDF.Node(blank=concept)
        # else if prefix is in our ns dict then create a URI node
        elif (prefix in ns):
            newnode = RDF.Node(RDF.Uri(ns[prefix]+concept))

    # if we don't have a node yet, then we need a literal node
    if (newnode is None):
        # TODO: If literal contains ^^ split it out as the type
        newnode = RDF.Node(literal=cell)

    return(newnode)

def addStatement(model, s, p, o):
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
    print(statement)
    model.add_statement(statement)

def createModel():
    storage=RDF.Storage(storage_name="hashes", name="geolink", options_string="new='yes',hash-type='memory',dir='.'")
    #storage=RDF.MemoryStorage()
    if storage is None:
        raise Exception("new RDF.Storage failed")
    model=RDF.Model(storage)
    if model is None:
        raise Exception("new RDF.model failed")
    return model

def serialize(model, ns, filename, format):
    # Format can be one of:
    # rdfxml          RDF/XML (default)
    # ntriples        N-Triples
    # turtle          Turtle Terse RDF Triple Language
    # trig            TriG - Turtle with Named Graphs
    # rss-tag-soup    RSS Tag Soup
    # grddl           Gleaning Resource Descriptions from Dialects of Languages
    # guess           Pick the parser to use using content type and URI
    # rdfa            RDF/A via librdfa
    # nquads          N-Quads
    if format==None:
        format="turtle"
    serializer=RDF.Serializer(name=format)
    for prefix in ns:
        serializer.set_namespace(prefix, RDF.Uri(ns[prefix]))
    serializer.serialize_model_to_file(filename, model)

def main():
    rdf_file_prefix = "obs-model-examples"
    model = createModel()
    ns = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "owl": "http://www.w3.org/2002/07/owl#"
    }

    add_statements_from_csv("sargasso-lipids-obs-model.csv", model, ns)

    print("Model size before serialize: " + str(model.size()))

    print("Serialize as TTL file...")
    serialize(model, ns, rdf_file_prefix + ".ttl", "turtle")
    print
    #print("Serialize as RDFXML file...")
    #serialize(model, ns, rdf_file_prefix + ".rdf", "rdfxml")

if __name__ == "__main__":
    import RDF
    import urllib2
    import xml.etree.ElementTree as ET
    import uuid
    import csv
    main()
