""" annotation.py

    The Annotation class tracks state and performs actions relevant to
    processing a dataset annotation from a CSV template.
"""

import os
import sys
import csv
import re
import pandas
import requests
import RDF
from urlparse import urlparse

from csvtotriples import rdfutils


class Annotation:
    def __init__(self, template, nrows=None):
        print "Loading annotation template from file: %s." % template

        self.template = template
        self.dataset = None
        self.nrows = nrows
        self.model = rdfutils.createModel() # An RDF Model

        # Store annotation template as a number of a dicts/arrays
        self.meta = {}
        self.ns = {}
        self.triples = []
        self.observations = {}
        self.contexts = {}
        self.measurements = {}
        self.entities = {}
        self.characteristics = {}
        self.standards = {}
        self.conversions = {}
        self.datatypes = {}
        self.mappings = []


    def __str__(self):
        outstring = "Current model size is %d." % self.model.size()

        return outstring


    def size(self):
        """ Returns the number of statements in the RDF Model"""

        return self.model.size()


    def addStatement(self, s, p, o):
        """ Custom addStatement override to make RDF statements as easy as
            possible to add to the graph.

            This method has the following features:

            - Converts strings into RDF.Uri's if they match foo:Thing
            - Converts subjects and predicates to RDF.Uri's if they aren't
                of type RDF.Node
        """

        # Subject
        if type(s) is str:
            s_parts = s.split(":")

            if len(s_parts) == 2:
                if s_parts[0] == "_":
                    s = RDF.Node(blank=s_parts[1])
                else:
                    s = RDF.Uri(self.ns[s_parts[0]] + s_parts[1])
            else:
                s = RDF.Uri(s)

        # Predicate
        if type(p) is str:
            p_parts = p.split(":")

            if len(p_parts) == 2:
                p = RDF.Uri(self.ns[p_parts[0]] + p_parts[1])
            else:
                p = RDF.Uri(p)

        # Object
        if type(o) is str:
            o_parts = o.split(":")

            if len(o_parts) == 2:
                if o_parts[0] == "_":
                    o = RDF.Node(blank=o_parts[1])
                else:
                    o = RDF.Uri(self.ns[o_parts[0]] + o_parts[1])
            else:
                o = RDF.Node(s)

        # Add the statement
        statement = RDF.Statement(s, p, o)

        if statement is None:
            raise Exception("Creating of new RDF.Statement failed.")

        self.model.add_statement(statement)


    def parse(self):
        """ Parse the annotation template file. Triples that don't need to look
        at the data are created here but triples that do need to look at the
        data are generated in the process() method.
        """

        if not os.path.isfile(self.template):
            raise Exception("Could not find the template file located at %s." % self.template)

        f = open(self.template, "rbU")
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

            # Skip lines that start with a '#'
            if len(row[0]) > 0 and row[0][0] == "#":
                continue

            # Remove cells that are comments (#)
            ncols = len(row)
            for i in range(0, ncols):
                if row[i].startswith("#"):
                    row[i] = ""


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
                    self.addMeta(row)

                elif state == "NAMESPACES":
                    self.addNamespace(row)

                elif state == "TRIPLES":
                    self.addTriple(row)

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
                        self.addObservation(row)
                    # Measurements/Entities/etc are at indent 2
                    elif len(stack) == 2:
                        parent = stack[0][1]
                        node_type = row[1]

                        if node_type == "entity":
                            self.addEntity(row, parent)
                        elif node_type == "measurement":
                            self.addMeasurement(row, parent)
                        elif node_type == "context":
                            self.addContext(row, parent)
                    elif len(stack) == 3:
                        parent = stack[1][1]
                        node_type = row[2]

                        if node_type == "characteristic":
                            self.addCharacteristic(row, parent)
                        elif node_type == "standard":
                            self.addStandard(row, parent)
                        elif node_type == "conversion":
                            self.addConversion(row, parent)
                        elif node_type == "datatype":
                            self.addDatatype(row, parent)


                elif state == "MAPPINGS":
                    self.addMapping(row)

        f.close()


    def process(self):
        """ Processes what has been read in from the parse() method."""

        # Add triples that have been parsed
        # TODO

        # Download the data file, if necessary
        if 'data_identifier' in self.meta:
            print "Processing data_identifier"

            url = self.meta['data_identifier']
            parsed_url = urlparse(url)
            parsed_paths = parsed_url.path.split('/')
            filename = parsed_paths[len(parsed_paths)-1]

            # Check if file exists in the current directory
            # If not, download and save
            if not os.path.isfile(filename):
                r = requests.get(url)

                if r.status_code != 200:
                    raise Exception("Status code was not 200. Download must have failed.")

                with open(filename, "wb") as f:
                    f.write(r.text)

                print "Retreiving data from url: %s" % url

            # Load the data file with pandas (autodetect format)
            with open(filename, "rb") as f:
                header_line = f.readline()

                if len(header_line.split(",")) > 1:          #CSV
                    self.dataset = pandas.read_fwf(filename)
                elif len(header_line.split("\t")) > 1:       # TSV
                    self.dataset = pandas.read_table(filename)
                else:
                    self.dataset = pandas.read_fwf(filename) #FWF

        if self.dataset is None:
            raise Exception("No dataset loaded. Somethingn went wrong.")

        # Process the mappings present
        index = 1

        for mapping in self.mappings:
            self.processMapping(mapping, index)
            index += 1


    def addMeta(self, row):
        self.meta[row[0]] = row[1]


    def addNamespace(self, row):
        if len(row[0]) < 1 or len(row[1]) < 1:
            return

        self.ns[row[0]] = row[1]


    def addTriple(self, row):
        """ Adds the triple in a row.
            Triples can be (URI, URI, URI) or (URI, URI, owl:unionOf(URI URI))
            Note that a space separates the two URIs and not a comma.
            TODO: Totally re-do addStatement stuff and this method in particular.
        """


        if len(row[0]) < 1 or len(row[1]) < 1 or len(row[2]) < 1:
            return

        self.triples.append([row[0], row[1], row[2]])


    def createUnionOfNode(self, node):
        """ Create a unionOf class node.

            Takes as input `node`, which is the unprocessed text from the CSV.
            With this text, we create and add nodes to the graph and return
                a reference to the first element in the unionOf set.

            owl:unionOf is handled in the following fashion:

            - Create blank nodes for each union class (A, B, C, etc...)
                - For each union class bnode, create another bnode CA
                    - To this bnode (CA), add two properties:
                        - rdf:first <A>
                        - rdf:rest #rdfnil
            - Return the first union class' bnode (A)

        """

        match_result = re.search("owl:unionOf\(([\w\s:]+)\)", node)

        if match_result is None:
            print "Error while parsing row with unionOf statement."
            print "Row was %s." % row
            print "No triples added for statement."

            return node

        # Split the string 'foo:Thing1 foo:Thing2' into [foo:Thing1, foo:Thing2, etc...]
        union_class_uri_strings = match_result.group(1).split(" ")

        # Stores union member blank nodes
        container_nodes = []

        for class_uri_string in union_class_uri_strings:
            print "Creating wrapper node for %s." % class_uri_string

            container_node = RDF.Node()
            container_nodes.append(container_node)

            # Add just the first statements now
            self.addStatement(container_node, 'rdf:first', class_uri_string)

        if len(container_nodes) < 1:
            print "Something went wrong when creating nodes for a unionOf statement. Result may be incorrect."
            return node

        # rdf:rest Statements

        # rdf:rest statements for 1:(n-1)
        for i in range(len(container_nodes)-1):
            self.addStatement(container_nodes[i], 'rdf:rest', container_nodes[i+1])

        # rdf:rest statement for n
        last_container_node = container_nodes[len(container_nodes) - 1]
        self.addStatement(last_container_node, 'rdf:rest', 'rdf:nil')

        # Create wrapper for the union
        union_node = RDF.Node()
        self.addStatement(union_node, 'rdf:type', 'owl:Class')
        self.addStatement(union_node, 'owl:unionOf', container_nodes[0])

        return union_node


    def addObservation(self, row):
        """This method doesn't do anything currently."""


    def addEntity(self, row, parent):
        if len(row[2]) < 1:
            return

        self.entities[parent] = row[2]


    def addMeasurement(self, row, parent):
        """ Add a mapping between a measurement template and an observation
            template

            row[2] is a key like m2
            parent is a key like o2
        """

        self.measurements[row[2]] = parent # TODO: Do I need this anymore?
        self.observations[row[2]] = parent


    def addCharacteristic(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        self.characteristics[parent] = row[3]


    def addStandard(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        self.standards[parent] = row[3]


    def addConversion(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        self.conversions[parent] = row[3]


    def addContext(self, row, parent):
        if len(parent) < 1 or len(row[2]) < 1:
            return

        self.contexts[parent] = row[2]


    def addDatatype(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        self.datatypes[parent] = row[3]


    def processTriples(self):
        """ Adds each triple in self.triples to the model."""

        for triple in self.triples:
            s = triple[0]
            p = triple[1]
            o = triple[2]

            # Handle unionOf case, either in subject or object
            if s.startswith("owl:unionOf"):
                s = self.createUnionOfNode(s)
            elif o.startswith("owl:unionOf"):
                o = self.createUnionOfNode(o)

            self.addStatement(s, p, o)


    def processMapping(self, mapping, index):
        dataset = self.dataset
        attrib = mapping['attribute']

        if attrib not in dataset:
            print "Couldn't find attribute %s in dataset with columns %s. Moving to next row." % (attrib, dataset.columns)
            return

        # Do straight mapping for straight mappings
        if 'value' in mapping and 'condition' in mapping:
            # Find the mapping condition (lt, gt, etc)
            condition = row[2].split(" ")

            if len(condition) != 2:
                print "Condition format error. Expected three tokens, separated by a space. Moving to next row."
                return

            if condition[1] == "eq":
                matched_data = dataset[attrib][dataset[attrib] == int(condition[3])]
            elif condition[1] == "neq":
                matched_data = dataset[attrib][dataset[attrib] != int(condition[3])]
            elif condition[1] == "lt":
                matched_data = dataset[attrib][dataset[attrib] < int(condition[3])]
            elif condition[1] == "gt":
                matched_data = dataset[attrib][dataset[attrib] > int(condition[3])]
            elif condition[1] == "lte":
                matched_data = dataset[attrib][dataset[attrib] >= int(condition[3])]
            elif condition[1] == "gte":
                matched_data = dataset[attrib][dataset[attrib] <= int(condition[3])]
            else:
                print "Unrecognized comparison operator. Try one of eq|neq|lt|gt|lte|gte. Moving to next row."
                return
        else:
            matched_data = dataset[mapping['attribute']]

        # TODO: remove this out of development
        if self.nrows is not None:
            matched_data = matched_data[0:self.nrows]

        self.addValues(mapping, index, matched_data)


    def addValues(self, mapping, mapping_index, data):
        """ Add values, and all related nodes and properties.

            For a given value, we add information that...
                It is a Measurement
                    of a Characteristic
                    according to a Standard
                    using an (optional) converstion Standard
                It is part of an Observation
                    of an Entity
                    which may have some Context
        """

        mapping_value = None
        attrib = mapping['attribute']
        key = mapping['key']

        # Handle maps with values
        if 'value' in mapping:
            mapping_value = mapping['value']

        data_index = data.index

        for i in range(len(data)):
            measurement = "_:m%d_%d" % (mapping_index, data_index[i])

            # Value Mapping: Replace with mapping value if needed
            if mapping_value is None:
                node_value = str(data[i])
            else:
                node_value = str(mapping_value)

            # Datatype: Use RDF datatype, if present
            if key in self.datatypes:
                value_node = RDF.Node(literal=node_value, datatype=RDF.Uri(self.datatypes[key]))
            else:
                value_node = RDF.Node(literal=node_value)

            # Use language, if present
            # TODO

            # Create Observation
            observation = "_:" + self.observations[key] + "row" + str(data_index[i])
            self.addStatement(observation, 'rdf:type', 'oboe:Observation')
            self.addStatement(observation, 'rdf:label', RDF.Node(literal=observation))

            # Create Measurement
            self.addStatement(measurement, 'rdf:type', 'oboe:Measurement')
            self.addStatement(measurement, 'oboe:hasValue', value_node)
            self.addStatement(measurement, 'rdf:label', RDF.Node(literal=attrib))

            # Observation-hasMeasurement-Measurement
            self.addStatement(observation, 'oboe:hasMeasurement', measurement)

            # Observation-hasContext-Observation
            if self.measurements[key] in self.contexts:
                other_observation = "_:" + self.contexts[self.measurements[key]] + "row" + str(data_index[i])

                self.addStatement(observation, 'oboe:hasContext', other_observation)

            # Observation-ofEntity-Entity
            if self.observations[key] in self.entities:
                entity = "_:" + self.observations[key] + "_entity"

                self.addStatement(entity, 'rdf:type', self.entities[self.measurements[key]])
                self.addStatement(observation, 'oboe:ofEntity', entity)

            # Measurement-ofCharacteristic-Characteristic
            if key in self.characteristics:
                characteristic = measurement + "_characteristic"

                self.addStatement(characteristic, 'rdf:type', RDF.Uri(self.characteristics[key]))
                self.addStatement(measurement, 'oboe:ofCharacteristic', characteristic)

            # Measurement-usesStandard-Standard
            if key in self.standards:
                standard = measurement + "_standard"

                self.addStatement(standard, 'rdf:type', self.standards[key])
                self.addStatement(measurement, 'oboe:usesStandard', standard)

            # Measurement-xxxx-Standard
            if key in self.conversions:
                conversion = measurement + "_conversion"

                self.addStatement(conversion, 'rdf:type', self.conversions[key])
                self.addStatement(measurement, 'foo:usesConversion', conversion)



    def addMapping(self, row):
        # Each mapping is at least an attribute/key pair.
        attrib = row[0]
        key = row[1]

        mapping = {}

        if len(row[0]) > 0:
            mapping['attribute'] = row[0]

        if len(row[1]) > 0:
            mapping['key'] = row[1]

        if len(row[2]) > 0:
            mapping['value'] = row[2]

        if len(row[3]) > 0:
            mapping['condition'] = row[3]

        self.mappings.append(mapping)


    def addDataType(self, row):
        if len(row[0]) < 1 or len(row[1]) < 1:
            return

        match = re.search("(.+):(.+)", row[1])
        if match is not None and len(match.groups()) == 2:
            namespace = match.group(1)
            datatype = match.group(2)

            full_uri = self.ns[namespace] + datatype

        else:
            print "Invalid datatype mapping."

        self.datatypes[row[0]] = full_uri


    def serialize(self, filename, format=None):
        if format == None:
            format = "turtle"

        serializer=RDF.Serializer(name=format)

        for prefix in self.ns:
            serializer.set_namespace(prefix, RDF.Uri(self.ns[prefix]))

        serializer.serialize_model_to_file(filename, self.model)
