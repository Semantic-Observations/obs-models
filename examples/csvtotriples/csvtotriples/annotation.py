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


    def nvalues(self):
        """ Returns the number of attribute:rownum pairs of values from
            mappings that should be present in the final graph.
        """

        count = 0

        for attribute in self.values:
            count += len(self.values[attribute])

        return count


    def addStatement(self, s, p, o, literal=False):
        """ Custom addStatement override to make RDF statements as easy as
            possible to add to the graph.

            This method has the following features:

            - Converts strings into RDF.Uri's if they match foo:Thing
            - Converts subjects and predicates to RDF.Uri's if they aren't
                of type RDF.Node

            Param `literal` specifies whether to treat the object as a literal
            node.
        """

        # Check types of s, p, and o before continuing
        if type(s) not in [RDF.Node, RDF.Uri, str]:
            raise Exception("Subject of triple not Node, Uri, or string.")

        if type(p) not in [RDF.Node, RDF.Uri, str]:
            raise Exception("Predicate of triple not Node, Uri, or string.")

        if type(o) not in [RDF.Node, RDF.Uri, str]:
            raise Exception("Object of triple not Node, Uri, or string.")


        # Process subject
        if type(s) is str:
            s_parts = s.split(":")

            if len(s_parts) == 2:
                if s_parts[0] == "_":
                    s = RDF.Node(blank=s_parts[1])
                else:
                    s = RDF.Uri(self.ns[s_parts[0]] + s_parts[1])
            else:
                s = RDF.Uri(s)

        # Process predidcate
        if type(p) is str:
            p_parts = p.split(":")

            if len(p_parts) == 2:
                p = RDF.Uri(self.ns[p_parts[0]] + p_parts[1])
            else:
                p = RDF.Uri(p)

        # Process object
        if type(o) is str:
            if not literal:
                o_parts = o.split(":")

                if len(o_parts) == 2:
                    if o_parts[0] == "_":
                        o = RDF.Node(blank=o_parts[1])
                    else:
                        o = RDF.Uri(self.ns[o_parts[0]] + o_parts[1])
                else:
                    o = RDF.Node(o)
            else:
                o = RDF.Node(literal=o)

        # Add the statement
        statement = RDF.Statement(s, p, o)

        if statement is None:
            raise Exception("Creating of new RDF.Statement failed.")

        self.model.add_statement(statement)


    def createUnionOfNode(self, node):
        """ Create a unionOf class node.

            Takes as input `node`, which is the unprocessed text from the CSV.

                e.g., 'owl:unionOf(foo:Entity bar:Entity)'

            With this text, we create and add nodes and stateemtns to the graph
            and return a reference to the RDF Container node so the triple
            containing the owl:unionOf subject or object can be completed.

            To parse the following subject or object:

                'owl:unionOf(foo:Entity bar:Entity)',

            we do the following:

            - Parse the `node` string to get the list of URI strings
              `[foo:Entity', 'bar:Entity']`
            - For each URI string
                - Create container RDF.Node()
                - Save a reference to it for later
                - Add an rdf:first statement pointing to the URI string
            - For all but the last container node
                - Add an rdf:rest statement which points to the next URI string
                  container node. (i.e., 1->2, 2->3, etc)
            - For the last container node
                - Add an rdf:rest statement of rdf:nil
            - Create another container node that will wrap the containers
                - Type it as an owl:Class
                - Add an owl:unionOf statement to the first container node
            - Return the outside container node as a reference

            The above steps produce the blank node (in TTL format):

                [
                    a owl:Class ;
                    owl:unionOf (foo:Entity
                        bar:Entity
                    )
                ]
        """

        match_result = re.search("owl:unionOf\(([\w\s:]+)\)", node)

        if match_result is None:
            print "Error while parsing row with unionOf statement."
            print "Row was %s." % row
            print "No triples added for statement."

            return node

        # Parse out the list of URI strings
        union_class_uri_strings = match_result.group(1).split(" ")

        # Keep track of URI string container nodes
        container_nodes = []

        for class_uri_string in union_class_uri_strings:
            container_node = RDF.Node()
            container_nodes.append(container_node)

            self.addStatement(container_node, 'rdf:first', class_uri_string)

        # Check to make sure we have two URI strings in our statement
        if len(container_nodes) < 2:
            print "Something went wrong when creating nodes for a unionOf statement. Result may be incorrect."
            return node

        # Add rdf:rest Statements

        # rdf:rest statements for 1:(n-1)
        for i in range(len(container_nodes)-1):
            self.addStatement(container_nodes[i], 'rdf:rest', container_nodes[i+1])

        # rdf:rest statement for n
        last_container_node = container_nodes[len(container_nodes) - 1]
        self.addStatement(last_container_node, 'rdf:rest', 'rdf:nil')


        # Create wrapper node for the union
        union_node = RDF.Node()
        self.addStatement(union_node, 'rdf:type', 'owl:Class')
        self.addStatement(union_node, 'owl:unionOf', container_nodes[0])

        return union_node


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

            if re.match("META|NAMESPACES|TRIPLES|OBSERVATIONS|MAPPING", header):
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
                # Do the work in between headers
                if state == "META":
                    self.parseMeta(row)
                elif state == "NAMESPACES":
                    self.parseNamespace(row)
                elif state == "TRIPLES":
                    self.parseTriple(row)
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
                        self.parseObservation(row)
                    # Measurements/Entities/etc are at indent 2
                    elif len(stack) == 2:
                        parent = stack[0][1]
                        node_type = row[1]

                        if node_type == "entity":
                            self.parseEntity(row, parent)
                        elif node_type == "measurement":
                            self.parseMeasurement(row, parent)
                        elif node_type == "context":
                            self.parseContext(row, parent)
                    # Characteristic/Standard/Conversion/etc are at indent 3
                    elif len(stack) == 3:
                        parent = stack[1][1]
                        node_type = row[2]

                        if node_type == "characteristic":
                            self.parseCharacteristic(row, parent)
                        elif node_type == "standard":
                            self.parseStandard(row, parent)
                        elif node_type == "conversion":
                            self.parseConversion(row, parent)
                        elif node_type == "datatype":
                            self.parseDatatype(row, parent)
                elif state == "MAPPINGS":
                    self.parseMapping(row)

        f.close()


    def process(self):
        """ Processes what has been read in from the parse() method.

            There are 3 major steps in this method.

            1. Download+load dataset (optional)
            2. Add parsed triples from TRIPLES section into Model
            3. Process all data mappings
        """

        # Download (if necessary) and load data
        if 'data_identifier' in self.meta:
            url = self.meta['data_identifier']
            parsed_url = urlparse(url)

            """ Check whether file is local or remote.
                The check used here is whether urlparse() extracts a scheme."""

            if len(parsed_url[0]) > 0:
                # Remote file
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

                    print "Retreiving data from URL: %s" % url
            else:
                # Local file

                # Raise exception if the data_identifier doesn't exist
                if not os.path.isfile(url):
                    raise Exception("data_identifier found but couldn't download or locate on disk: %s" % url)

                filename = url

            # Load the data file with pandas (autodetect format)
            with open(filename, "rb") as f:
                header_line = f.readline()

                if len(header_line.split(",")) > 1:          #CSV
                    self.dataset = pandas.read_csv(filename)
                elif len(header_line.split("\t")) > 1:       # TSV
                    self.dataset = pandas.read_table(filename)
                else:
                    self.dataset = pandas.read_fwf(filename) #FWF

            # Trim the dataset to only the number of rows the user specified
            if self.nrows is not None:
                self.dataset = self.dataset[0:self.nrows]
            else:
                self.nrows = self.dataset.shape[0]

            # Set up value tracking dict
            self.values = {}

            for attribute in self.dataset.columns:
                self.values[attribute] = set([])


        # Process triples
        self.processTriples()

        # Process the mappings present
        index = 1

        for mapping in self.mappings:
            self.processMapping(mapping, index)
            index += 1


        self.validate()


    def validate(self):
        """ Perform validations on the annotation.

        """


        self.validateValueUse()


    def validateValueUse(self):
        """ Check if we added all the values we were supposed to.
            Each attribute should have exactly 'self.nrows' values in it
        """


        if self.dataset is not None:
            for attribute in self.values:
                expected = self.nrows
                actual = len(self.values[attribute])

                if actual > expected:
                    raise Exception("Too many values used from attribute %s. (Expected %d, Actual %s)" % (attribute, expected, actual))
                elif actual < expected:
                    raise Exception("Too few values used from attribute %s. (Expected %d, Actual %s)" % (attribute, expected, actual))


    def parseMeta(self, row):
        """ Validate and parse a row from the META section.

            e.g., row = ['metadata_identifier', 'some_url']
        """


        if len(row) < 2 or len(row[0]) < 1 or len(row[1]) < 1:
            print "Warning: Failed to parse row from META section: `%s`." % row

            return


        self.meta[row[0]] = row[1]


    def parseNamespace(self, row):
        """ Validate and parse a row from the NAMESPACE section.

            e.g., row = ['foo', 'http://myfoo.com/foo#']
        """


        if len(row) < 2 or len(row[0]) < 1 or len(row[1]) < 1:
            print "Warning: Failed to parse row from NAMESPACE section: `%s`." % row

            return


        self.ns[row[0]] = row[1]


    def parseTriple(self, row):
        """ Validate and parse a row from the TRIPLES section.

            e.g., row = ['foo:Entity', 'owl:equivalentClass', 'bar:Entity']
        """


        if len(row) < 3 or len(row[0]) < 1 or len(row[1]) < 1 or len(row[2]) < 1:
            print "Warning: Failed to parse row from TRIPLES section: `%s`." % row

            return

        self.triples.append([row[0], row[1], row[2]])


    def parseObservation(self, row):
        """ Validate and parse a row from the OBSERVATIONS section.

            e.g., row = ['observation', 'o1', '', '']
        """

        if len(row) < 3 or len(row[0]) < 1 or len(row[1]) < 1:
            print "Warning: Failed to parse row from TRIPLES section: `%s`." % row

            return


    def parseEntity(self, row, parent):
        """ Validate and parse a row containing an Entity statement from within
            the OBSERVATIONS section.

            e.g., row = ['', 'entity', 'foo:SomeEntity', '']
        """

        if len(row) < 3 or len(row[1]) < 1 or len(row[2]) < 1:
            print "Warning: Failed to parse Entity row: `%s`." % row

            return

        self.entities[parent] = row[2]


    def parseMeasurement(self, row, parent):
        """ Validate and parse a row containing a Measurement statement from
            within the OBSERVATIONS section.

            e.g., row = ['', 'measurement', 'm1', '']
        """

        if len(row) < 3 or len(row[1]) < 1 or len(row[2]) < 1:
            print "Warning: Failed to parse Measurement row: `%s`." % row

            return

        self.measurements[row[2]] = parent # TODO: Do I need this anymore?
        self.observations[row[2]] = parent


    def parseCharacteristic(self, row, parent):
        """ Validate and parse a row containing a Characteristic statement from
            within the OBSERVATIONS section.

            e.g., row = ['', '', 'characteristic', 'foo:SomeCharacteristic']
        """

        if len(row) < 4 or len(row[2]) < 1 or len(row[3]) < 1:
            print "Warning: Failed to parse Characteristic row: `%s`." % row

            return


        self.characteristics[parent] = row[3]


    def parseStandard(self, row, parent):
        """ Validate and parse a row containing a Standard statement from
            within the OBSERVATIONS section.

            e.g., row = ['', '', 'standard', 'foo:SomeStandard']
        """

        if len(row) < 4 or len(row[2]) < 1 or len(row[3]) < 1:
            print "Warning: Failed to parse Standard row: `%s`." % row

            return


        self.standards[parent] = row[3]


    def parseConversion(self, row, parent):
        """ Validate and parse a row containing a Conversion statement from
            within the OBSERVATIONS section.

            e.g., row = ['', '', 'conversion', 'foo:SomeConversion']
        """

        if len(row) < 4 or len(row[2]) < 1 or len(row[3]) < 1:
            print "Warning: Failed to parse Conversion row: `%s`." % row

            return


        self.conversions[parent] = row[3]


    def parseDatatype(self, row, parent):
        """ Validate and parse a row containing a Datatype statement from
            within the OBSERVATIONS section.

            e.g., row = ['', '', 'datatype', 'xsd:decimal']
        """

        if len(row) < 4 or len(row[2]) < 1 or len(row[3]) < 1:
            print "Warning: Failed to parse Datatype row: `%s`." % row

            return


        self.datatypes[parent] = row[3]


    def parseContext(self, row, parent):
        """ Validate and parse a row containing a Context statement from
            within the OBSERVATIONS section.

            e.g., row = ['', 'context', 'o2', '']
        """

        if len(row) < 3 or len(row[1]) < 1 or len(row[2]) < 1:
            print "Warning: Failed to parse Context row: `%s`." % row

            return


        self.contexts[parent] = row[2]


    def parseMapping(self, row):
        """ Validate and parse a row from the MAPPINGS section.

            e.g., row = ['site', 'm1', '', '']
                  row = ['spp', 'm2', 'spp eq shad', 'Alosa sapidissima']
        """

        if len(row) < 2 or len(row[0]) < 1 or len(row[1]) < 1:
            print "Warning: Failed to parse Mapping row: `%s`." % row

            return


        # Each mapping is at least an attribute/key pair.
        attrib = row[0]
        key = row[1]

        mapping = {}

        if len(row[0]) > 0:
            mapping['attribute'] = row[0]

        if len(row[1]) > 0:
            mapping['key'] = row[1]

        if len(row[2]) > 0:
            mapping['condition'] = row[2]

        if len(row[3]) > 0:
            mapping['value'] = row[3]

        self.mappings.append(mapping)


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
        """ Process a attribute-measurement mapping.

            `mapping` is a Dict containing keys:

                Required:
                    - attribute: Column in the data, e.g. spp
                    - key: Measurement template key, e.g. m2

                Optional:
                    - condition: String for the condition, e.g., 'spp eq shad'
                    - value: String for the replacement value, e.g., 'Alosa sapidissima'

            This method checks if the attribute is in the dataset (as a column)
            and then perform either an unconditional or conditional mapping.
        """


        dataset = self.dataset
        attrib = mapping['attribute']

        if attrib not in dataset:
            print "Couldn't find attribute %s in dataset with columns %s. Moving to next row." % (attrib, dataset.columns)
            return

        # Do straight mapping for straight mappings
        if 'condition' in mapping and 'value' in mapping:
            # Find the mapping condition (lt, gt, etc)
            condition = mapping['condition'].split(" ")

            if len(condition) != 3:
                print "Condition format error. Expected three tokens, separated by a space. Moving to next row. Found %s." % mapping
                return

            if condition[1] == "eq":
                matched_data = dataset[attrib][dataset[attrib] == condition[2]]
            elif condition[1] == "neq":
                matched_data = dataset[attrib][dataset[attrib] != condition[2]]
            elif condition[1] == "lt":
                matched_data = dataset[attrib][dataset[attrib] < condition[2]]
            elif condition[1] == "gt":
                matched_data = dataset[attrib][dataset[attrib] > condition[2]]
            elif condition[1] == "lte":
                matched_data = dataset[attrib][dataset[attrib] >= condition[2]]
            elif condition[1] == "gte":
                matched_data = dataset[attrib][dataset[attrib] <= condition[2]]
            else:
                print "Unrecognized comparison operator. Try one of eq|neq|lt|gt|lte|gte. Moving to next row. Found %s." % condition[1]
                return
        else:
            matched_data = dataset[mapping['attribute']]

        self.addValues(mapping, index, matched_data)


    def addValues(self, mapping, mapping_index, data):
        """ Adds values from the dataset to the Model.

            Blank nodes are used throughout this method to link statements. A
            common format for the blank node identifier is followed:

                Observations start with '_:o...'
                Measurements start with '_:m...'
                etc.

                '_:o1...' is used for values from the Observation keyed as 'o1', and
                so on.

            Because each row contains one or more Observations and blank node
            identifiers need to be unique, we append the row number to the
            identifier, e.g., '_:o1_row0' for the first row.

            Blank node identifiers for Measurements, Entities, and
            Characteristics have a string appended to their identifier, e.g.,

                '_:m1_row0_characteristic'

            A similar pattern is followed for other concepts.
        """

        mapping_value = None
        attrib = mapping['attribute']
        key = mapping['key']

        # Handle maps with values
        if 'value' in mapping:
            mapping_value = mapping['value']

        data_index = data.index

        for i in range(len(data)):
            # Keep track of adding this value to the graph
            self.trackUseOfValue(attrib, i)

            # Create measurement blank node identifier
            measurement = "_:m%d_row%d" % (mapping_index, data_index[i])

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


            # Create Measurement
            self.addStatement(measurement, 'rdf:type', 'oboe:Measurement')
            self.addStatement(measurement, 'oboe:hasValue', value_node)
            self.addStatement(measurement, 'rdf:label', RDF.Node(literal=attrib))

            # Create Observation
            if key in self.observations:
                observation = "_:" + self.observations[key] + "row" + str(data_index[i])
                self.addStatement(observation, 'rdf:type', 'oboe:Observation')
                self.addStatement(observation, 'rdf:label', RDF.Node(literal=observation))

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

            # TODO: Conversions
            # if key in self.conversions:


    def trackUseOfValue(self, attribute, row_num):
        """ Track the use of `row_num` in column `attribute` in the dataset.

            This is done to tell the user whether they added:
                - All the data they meant to
                - Each value only once
        """

        if attribute not in self.values:
            raise Exception("Invalid attribute to track the use of values for. (%s)" % attribute)

        if row_num in self.values[attribute]:
            raise Exception("Attempted to use a value we've already added. (attribute: %s, row num: %s)" % (attribute, row_num))

        if row_num not in self.values[attribute]:
            self.values[attribute].add(row_num)


    def serialize(self, filename, format=None):
        """ Serialize the Model to file. """


        if format == None:
            format = "turtle"

        serializer=RDF.Serializer(name=format)

        for prefix in self.ns:
            serializer.set_namespace(prefix, RDF.Uri(self.ns[prefix]))

        serializer.serialize_model_to_file(filename, self.model)
