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
        self.mappings = []


    def __str__(self):
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


                elif state == "MAPPINGS":
                    # Each mapping is at least an attribute/key pair.
                    attrib = row[0]
                    key = row[1]

                    dataset = self.dataset

                    if attrib not in dataset:
                        print "Couldn't find attribute %s in dataset with columns %s. Moving to next row." % (attrib, dataset.columns)
                        continue

                    # Do straight mapping for straight mappings
                    if len(''.join(row[2:]).strip()) == 0:
                        self.mappings.append([row[0], row[1]])

                        matched_data = dataset[attrib]

                    # Otherwise, do conditional mapping
                    else:
                        self.mappings.append([row[0], row[1], row[2], row[3]])

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

                    self.addValues(key, row, matched_data[0:4])

                # f.close()

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
        self.ns[row[0]] = row[1]


    def addTriple(self, row):
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
        print "Adding characteristic of %s to %s." % (row[3], parent)

        if parent not in self.characteristics:
            self.characteristics[parent] = []

        self.characteristics[parent].append(row[3])


    def addStandard(self, row, parent):
        print "Adding standard of %s to %s." % (row[3], parent)

        if parent not in self.standards:
            self.standards[parent] = []

        self.standards[parent].append(row[3])


    def addContext(self, row, parent):
        print "context...<<stub>>"


    def addValues(self, key, row, data):
        print "values...<<stub>>"

        mapping_value = None

        # Handle maps with values
        if len(row) == 4 and len(row[2].strip()) > 0:
            print "Mapping with value %s." % row[2]
            mapping_value = row[2]

        data_index = data.index

        for i in range(0, len(data)):
            identifier =  key + '-' + str(len(self.mappings)) + '-' + str(data_index[i])
            print identifier

            s = RDF.Node(blank=identifier)
            p = RDF.Uri(self.ns['oboe']+'hasValue')

            if mapping_value is None:
                o = RDF.Node(literal=str(data[i]))
            else:
                o = RDF.Node(literal=str(mapping_value))

            rdfutils.addStatement(self.model, s, self.ns['rdf']+'type', RDF.Uri(self.ns['oboe']+'Measurement'))
            rdfutils.addStatement(self.model, s, p, o)

            print self.characteristics
            # Add characteristics
            if key in self.characteristics:
                for characteristic in self.characteristics[key]:
                    print "Statement characteristic %s for %s." % (characteristic, key)

                    rdfutils.addStatement(self.model, s, self.ns['oboe']+'ofCharacteristic', RDF.Uri(characteristic))

            # Add standards
            if key in self.standards:
                for standard in self.standards[key]:
                    print "Statement standard %s for %s." % (standard, key)

                    rdfutils.addStatement(self.model, s, self.ns['oboe']+'usesStandard', RDF.Uri(standard))



    def addMapping(self, row):
        print "mapping...<<stub>>"


    def serialize(self, filename, format=None):
        if format == None:
            format = "turtle"

        serializer=RDF.Serializer(name=format)

        for prefix in self.ns:
            serializer.set_namespace(prefix, RDF.Uri(self.ns[prefix]))

        serializer.serialize_model_to_file(filename, self.model)
