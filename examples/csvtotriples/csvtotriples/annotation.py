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
    def __init__(self, template):
        print "Loading annotation template from file: %s." % template

        self.template = template
        self.model = rdfutils.createModel() # An RDF Model

        # Store annotation template as a number of a dicts/arrays
        self.meta = {}
        self.ns = {}
        self.triples = []
        self.observations = {}
        self.measurements = {}
        self.entities = {}
        self.characteristics = {}
        self.standards = {}
        self.conversions = {}
        self.datatypes = {}
        self.mappings = []


    def __str__(self):
        outstring = "annotation"

        return outstring


    def process(self):
        f = open(self.template, "rbU")
        reader = csv.reader(f)


        """ Store annotation information in a dict, which we will return. """

        annotation = {}


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
                elif header == "DATATYPES":
                    state = "DATATYPES"
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


                elif state == "MAPPINGS":
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

                elif state == "DATATYPES":
                    self.addDataType(row)

        f.close()

        self.processMappings()


    def addMeta(self, row):
        self.meta[row[0]] = row[1]

        if row[0] == 'data_identifier':
            url = row[1]
            parsed_url = urlparse(url)
            parsed_paths = parsed_url.path.split('/')
            filename = parsed_paths[len(parsed_paths)-1]

            # Check if file exists in the current directory
            # If not, download and save
            if not os.path.isfile(filename):
                r = requests.get(url)

                if r.status_code != 200:
                    print "Status code was not 200. Download must have failed."
                    sys.exit()

                with open(filename, "wb") as f:
                    f.write(r.text)

                print "Retreiving data from url: %s" % url

            self.dataset = pandas.read_fwf(filename)


    def addNamespace(self, row):
        if len(row[0]) < 1 or len(row[1]) < 1:
            return

        self.ns[row[0]] = row[1]


    def addTriple(self, row):
        if len(row[0]) < 1 or len(row[1]) < 1 or len(row[2]) < 1:
            return

        s = row[0]
        p = row[1]
        o = row[2]

        # Make URIs when of form x:y
        if s.find(":") >= 0:
            s = RDF.Uri(s)

        if p.find(":") >= 0:
            p = RDF.Uri(p)

        if o.find(":") >= 0:
            o = RDF.Uri(o)

        rdfutils.addStatement(self.model, s, p, o)
        self.triples.append((s, p, o))


    def addObservation(self, row):
        if len(row[1]) < 1:
            return

        blank_node = RDF.Node(blank=row[1])

        # Save the bnode
        self.observations[row[1]] = blank_node

        # Add the triple
        rdfutils.addStatement(self.model,
                     blank_node,
                     RDF.Uri(self.ns["rdf"]+"type"),
                     RDF.Uri(self.ns["oboe"]+"Observation"))

        rdfutils.addStatement(self.model,
                     blank_node,
                     RDF.Uri(self.ns["rdf"]+"label"),
                     row[1])


    def addEntity(self, row, parent):
        if len(row[2]) < 1:
            return

        blank_node = RDF.Node(blank=row[2])

        # rdf:type
        rdfutils.addStatement(self.model,
                     blank_node,
                     RDF.Uri(self.ns["rdf"]+"type"),
                     RDF.Uri(self.ns["oboe"]+"Entity"))

        # oboe:ofEntity
        rdfutils.addStatement(self.model,
                     self.observations[parent],
                     RDF.Uri(self.ns["oboe"]+"ofEntity"),
                     blank_node)
        # rdf:label
        rdfutils.addStatement(self.model,
                     blank_node,
                     RDF.Uri(self.ns["rdf"]+"label"),
                     row[2])


    def addMeasurement(self, row, parent):
        print "measurement...<<stub>>"

        print row
        print parent


    def addCharacteristic(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        print "Adding characteristic of %s to %s." % (row[3], parent)

        if parent not in self.characteristics:
            self.characteristics[parent] = []

        self.characteristics[parent].append(row[3])


    def addStandard(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        print "Adding standard of %s to %s." % (row[3], parent)

        if parent not in self.standards:
            self.standards[parent] = []

        self.standards[parent].append(row[3])


    def addConversion(self, row, parent):
        if len(parent) < 1 or len(row[3]) < 1:
            return

        print "Adding conversion of %s to %s." % (row[3], parent)

        if parent not in self.conversions:
            self.conversions[parent] = []

        self.conversions[parent].append(row[3])


    def addContext(self, row, parent):
        if len(parent) < 1 or len(row[2]) < 1:
            return


        o1 = row[2]
        o2 = parent

        print "Adding context for %s of %s." % (o1, o2)

        # Create blank nodes for observations if needed
        if o1 not in self.observations:
            s = RDF.Node(blank=identifier)

            self.observations[o1] = s
            rdfutils.addStatement(self.model, s, self.ns['ns']+'type', RDF.Uri(self.ns['oboe']+'Observation'))

        if o2 not in self.observations:
            s = RDF.Node(blank=identifier)

            self.observations[02] = s
            rdfutils.addStatement(self.model, s, self.ns['ns']+'type', RDF.Uri(self.ns['oboe']+'Observation'))

        rdfutils.addStatement(self.model, self.observations[o1], self.ns['oboe']+'hasContext', self.observations[o2])


    def processMappings(self):

        index = 1

        for mapping in self.mappings:
            self.processMapping(mapping, index)
            index += 1


    def processMapping(self, mapping, index):
        dataset = self.dataset
        attrib = mapping['attribute']

        if attrib not in dataset:
            print "Couldn't find attribute %s in dataset with columns %s. Moving to next row." % (attrib, dataset.columns)
            return

        # Do straight mapping for straight mappings
        if 'value' in mapping and 'condition' in mapping:
            # Find the mapping condition (lt, gt, etc)
            condition = row[3].split(" ")

            if len(condition) != 3:
                print "Condition format error. Expected three tokens, separated by a space. Moving to next row."
                return

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
                return
        else:
            matched_data = dataset[mapping['attribute']]


        self.addValues(mapping, index, matched_data[0:4])


    def addValues(self, mapping, index, data):
        mapping_value = None
        attrib = mapping['attribute']
        key = mapping['key']


        # Handle maps with values
        if 'value' in mapping:
            print "Mapping with value %s." % mapping['value']
            mapping_value = mapping['value']

        data_index = data.index

        for i in range(0, len(data)):
            identifier = key + '-' + str(index) + '-' + str(data_index[i])
            print identifier

            blank_node = RDF.Node(blank=identifier)

            # Replace with mapping value if needed
            if mapping_value is None:
                node_value = str(data[i])
            else:
                node_value = str(mapping_value)


            # Use datatype, if present
            print "Searching for %s in datatypes." % mapping['attribute']

            if attrib in self.datatypes:
                value_node = RDF.Node(literal=node_value, datatype=RDF.Uri(self.datatypes[attrib]))
            else:
                value_node = RDF.Node(literal=node_value)


            # Use language, if present
            # TODO


            rdfutils.addStatement(self.model, blank_node, self.ns['rdf']+'type', RDF.Uri(self.ns['oboe']+'Measurement'))
            rdfutils.addStatement(self.model, blank_node, RDF.Uri(self.ns['oboe']+'hasValue'), value_node)




            # Add characteristics
            if key in self.characteristics:
                for characteristic in self.characteristics[key]:
                    print "Statement characteristic %s for %s." % (characteristic, key)

                    rdfutils.addStatement(self.model, blank_node, self.ns['oboe']+'ofCharacteristic', RDF.Uri(characteristic))

            # Add standards
            if key in self.standards:
                for standard in self.standards[key]:
                    print "Statement standard %s for %s." % (standard, key)

                    rdfutils.addStatement(self.model, blank_node, self.ns['oboe']+'usesStandard', RDF.Uri(standard))

            # Add conversions
            if key in self.conversions:
                for conversion in self.conversions[key]:
                    print "Statement conversion %s for %s." % (conversion, key)

                    rdfutils.addStatement(self.model, blank_node, self.ns['foo']+'hasConversion', RDF.Uri(conversion))



    def addMapping(self, row):
        print "mapping...<<stub>>"


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
