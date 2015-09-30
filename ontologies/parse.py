""" parse.py
    Matt Jones (jones@nceas.ucsb.edu)

    Parse a Turtle file into a model
"""

import RDF

if __name__ == "__main__":
    parser=RDF.TurtleParser()
    model = RDF.Model()
    parser.parse_into_model(model, "file:./union.ttl")
    print(model.size())
    for statement in model:
        print(statement)
