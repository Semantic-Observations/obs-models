#!/opt/local/bin/python
#
# A script to read RDF subject/triple/object properties form a csv file and turn them into RDF models
#
# Matt Jones and Adam Shepherd

def add_statements_from_csv(filename, model, ns):

    cfile  = open(filename, "rb")
    reader = csv.reader(cfile)

    triple_section = False
    ns_section = False
    rownum = 0
    for row in reader:
        rownum = rownum+1
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
            
            # TODO: parse the cell value to determine if it is a blank node or a prefix:class, then turn them into proper nodes
            
            # TODO: add a Statement to the model with the s, p, o
        model.sync()
            
    cfile.close()
    
def addStatement(model, s, p, o):
    if (type(o)!="RDF.Node"):
        obj = RDF.Node(o)
    else:
        obj = o
    statement=RDF.Statement(RDF.Uri(s), RDF.Uri(p), obj)
    if statement is None:
        raise Exception("new RDF.Statement failed")
    model.add_statement(statement)
    
def addDataset(model, doc, ns, personhash):
    d1base = "https://cn.dataone.org/cn/v1/resolve/"
    element = doc.find("./str[@name='identifier']")
    identifier = element.text
    addStatement(model, d1base+identifier, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", RDF.Uri(ns["gldata"]+"DigitalObjectRecord"))
    addStatement(model, d1base+identifier, ns["dcterms"]+"identifier", identifier)
    title_element = doc.find("./str[@name='title']")
    addStatement(model, d1base+identifier, ns["dcterms"]+"title", title_element.text)
    
    originlist = doc.findall("./arr[@name='origin']/str")
    for creatornode in originlist:
        creator = creatornode.text
        if (creator not in personhash):
            # Add it
            newid = uuid.uuid4()
            p_uuid = newid.urn
            p_orcid = "http://fakeorcid.org/" + newid.hex
            p_data = [p_uuid, p_orcid]
            personhash[creator] = p_data
        else:
            # Look it up
            p_data = personhash[creator]
            p_uuid = p_data[0]
            p_orcid = p_data[1]
            
        addStatement(model, p_uuid, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", RDF.Uri(ns["glperson"]+"Person"))
        addStatement(model, p_uuid, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", RDF.Uri(ns["foaf"]+"Person"))
        addStatement(model, p_uuid, ns["foaf"]+"name", creator)
        
        pi_node = RDF.Node(RDF.Uri(p_orcid))
        s1=RDF.Statement(pi_node, RDF.Uri("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), RDF.Uri(ns["datacite"]+"PersonalIdentifier"))       
        model.add_statement(s1)
        s2=RDF.Statement(pi_node, RDF.Uri(ns["datacite"]+"usesIdentifierScheme"), RDF.Uri(ns["datacite"]+"orcid"))       
        model.add_statement(s2)
        s3=RDF.Statement(RDF.Uri(p_uuid), RDF.Uri(ns["datacite"]+"hasIdentifier"), pi_node)
        model.add_statement(s3)
        s4=RDF.Statement(RDF.Uri(d1base+identifier), RDF.Uri(ns["dcterms"]+"creator"), RDF.Uri(p_uuid))
        model.add_statement(s4)
        model.sync()

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
        print("Adding NS prefix: " + prefix)
        serializer.set_namespace(prefix, RDF.Uri(ns[prefix]))
    serializer.serialize_model_to_file(filename, model)

def main():
    rdf_file_prefix = "obs-model-examples"
    model = createModel()
    ns = {
        "foaf": "http://xmlns.com/foaf/0.1/",
        "dcterms": "http://purl.org/dc/terms/",
        "gldata": "http://schema.geolink.org/repository-object#",
        "glperson": "http://schema.geolink.org/person#",
        "glpersonii": "http://schema.geolink.org/personal-info-item#",
        "glpersonname": "http://schema.geolink.org/person-name#",
        "datacite": "http://purl.org/spar/datacite/"
    }
    
    add_statements_from_csv("sargasso-lipids-obs-model.csv", model, ns)
    
    print("Model size before serialize: " + str(model.size()))
    
    print("Serialize as TTL file...")
    serialize(model, ns, rdf_file_prefix + ".ttl", "turtle")
    print
    print("Serialize as RDFXML file...")
    serialize(model, ns, rdf_file_prefix + ".rdf", "rdfxml")

if __name__ == "__main__":
    import RDF
    import urllib2
    import xml.etree.ElementTree as ET
    import uuid
    import csv
    main()
