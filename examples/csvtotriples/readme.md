# CSV To Triples

`csvtotriples` automatically generate triples for a dataset according to an observations ontology using a custom template file.
For now, the annotation script and template only work with the OBOE ontology but wouldn't require significant modification to work with others.

The work of creating triples for an entire dataset can be done by hand but is tedious and time-consuming for larger datasets and the work is highly redundant. By using a template to describe the set of triples we wish to generate, this work becomes more efficient and potentially less error-prone.

## Usage

The script `annotate.py` takes the following arguments from the command line and generates a Turtle file of triples for your dataset.

- Filename (required)
- Number of rows (optional, defaults to all rows from the dataset)
- Output filename (optional, defaults to the same name as the annotation template filename plus '.ttl')

For example, if we have a template file called mydataset-template.csv, run the following:

```{sh}
python path/to/annotate.py mydataset-template.csv
```

The resulting triples will be written out to a file `mydataset-template.csv.ttl`. This will overwrite whatever is located in that file so be careful.

You may want to run the script with its additional command line arguments, like:

```{sh}
python path/to/annotate.py -n 5 -o mydataset.ttl mydataset-template.csv
```

The above command will only annotate the first five rows of the dataset and will write the result to `mydataset.ttl`.


The script `csvtotriples/skeleton.py` generates an empty (skeleton) annotation template and is a good place to start when creating an annotation template for a new dataset.


## Template File

The template file format was designed to make it easy to annotate a dataset with minimal repetition.

The file contains five sections which contain specific information relevant to the automatic annotation process:

- META: Identifiers for the metadata and data.
- NAMESPACES: Namespaces for the annotation graph.
- TRIPLES: Triples the user wants to manually specify. These are simply added directly to the graph.
- OBSERVATIONS: The observations the data are being annotated with.
- MAPPINGS: Mappings between a semantic concept and attributes of the data


Note: Any blank rows, rows that start with a #, or cells that start with a # will be ignored and can be helpful in documenting your template.

Each section is optional and each section may contain a number of values:

### META:

A set of tuples of relevant information about the dataset.

`metadata_identifier`: URI for the dataset's metadata

`data_identifier`: URI for the data itself. This URI should be resolvable and return the dataset.

Example:

```{csv}
META,,,
metadata_identifier,http://www.bco-dmo.org/dataset/3584,,
data_identifier,http://data.bco-dmo.org/jg/serv/BCO/vanMooy/SargassoSeaLipids/X1103_CTD_profiles.flat9,,
```

Other tuples can be placed here if it is useful for documentation or other purposes.
Only the content in the `dataset_identifier` tuple matters for program execution.


### NAMESPACES

Tuples of the form `namespace`,`URI`, e.g.:

`rdf,http://www.w3.org/1999/02/22-rdf-syntax-ns#`

Example:

```{csv}
NAMESPACES,,,
rdf,http://www.w3.org/1999/02/22-rdf-syntax-ns#,,
oboe,http://ecoinformatics.org/oboe/oboe.1.0/oboe-core.owl#,,
oboe-standard,http://ecoinformatics.org/oboe/oboe.1.0/oboe-standard.owl#,,
```


### TRIPLES

Subject-predicate-object triples, e.g.:

`owl:Thing,owl:equivalentClass,foo:MyThing`

Example:

```{csv}
TRIPLES,,,
oboe:Observation,owl:equivalentClass,oml:Observation,
```

The TRIPLES section supports subjects and objects that are `owl:unionOf` statements, like:

```{csv}
TRIPLES
foo:MyThing,owl:equivalentClass,owl:unionOf(foo:OneThing foo:AnotherThing),
owl:unionOf(foo:A foo:B),owl:equivalentClass,foo:C,
```


### OBSERVATIONS

This section contains a hierarchical description of OBOE Observations, Entities, Measurements, Characteristics, Standards, Conversions, and Contexts.
Blank/indented cells are used to encode the hierarchy.

```
observation , o1          ,                ,
            , entity      , foo:myentity   ,
            , measurement , m1             ,
            ,             , characteristic , foo:mycharacteristic
            ,             , standard       , foo:mystandard
            ,             , conversion     , foo:myconversion
            ,             , datatype       , xsd:decimal
            , context     , o2             ,

```

In the above code block, an Observation with key `o1` is of an Entity `e1`, has a Measurement `m1`, and a Context of Observation `o2`. The keys uniquely specify linkages between instances of concepts within the template.
In the above example, a lower case letter matching the first letter of the corresponding to a semantic concept (i.e. o for Observation)  is followed by a number but this is just used for clarity and the only requirement is that keys must be non-zero-length strings.
Moving one level of indentation (column) over to the right, the above code block specifies that Measurement `m1` is of a Characteristic `foo:mycharacteristic`, was measured according to Standard `foo:mystandard`, and has a Conversion `foo:myconversion` and all values should have the RDF datatype of `xsd:decimal`.

Example:

```{csv}
OBSERVATIONS,,,
#cast,,,
observation,o1,,
,entity,e1,domain:3DRelativeSite
,measurement,m1,
,,characteristic,domain:CastIdentifier
,,standard,domain:SargassoProjectCastIdentifiers
```

Note the row containing `#cast`. This is a comment and is a useful way to label the template file.
Also, the row `,measurement,m1` (above) isn't specifying that there will be one measurement for Observation `o1` but is instead saying that there is a Measurement template (with key `m1`) that describes the set of all Measurements taking during Observation `o1`.
Each of the Measurements in in the template were taking according to the same Standard and Characteristic.


### MAPPINGS

Either a tuple or a quad:

`attribute,key`
`attribute,key,condition,value`

For the first form, attributes (usually columns) of the data are mapped onto a semantic concept by its key (usually a measurement, e.g. m1).
For the second form, attributes are again mapped to semantic concepts but instead of the values being read from the data and inserted directly into the graph, as in the tuple form, the `value` is substituted from the mapping according to a condition.

For example, say you had data with the column `spp` which contained the species being measured. If the triples you wanted to generate were:

```{ttl}
[]
    oboe:hasValue "Oncorhynchus tshawytscha" ;
    a oboe:Measurement .
```

but the data had encoded the species using a common name, such as "King", we could handle this with the following mapping:

`spp,m3,spp eq Chinook,Oncorhynchus tshawytscha`

Example:

```{csv}
MAPPINGS,,,
date,m2,,
time,m3,,
spp,m3,spp eq Chinook,Oncorhynchus tshawytscha
```

Without a mapping covering values within the data, values from the data won't be entered into the graph.
Mappings select data from a column of the dataset and add the necessary triples for that value to the graph.
If no mappings are specified, no Measurements/Characteristics/Standards/etc will be added to the graph (and no values either)
If a conditional mapping is specified that doesn't cover all data in a column (i.e. `site,m10,SiteAlpha,site eq 1`), any values in the `site` column not equal to 1 won't be added to the graph.
All values in the dataset must correspond to a mapping, conditional or otherwise.


### DATATYPES

Tuples of the form `attribute,URI` where `URI` is the URI of a datatype, e.g. `xsd:decimal`.
These are optional and no datatype will be used for attributes without a datatype tuple.

Example:

```{csv}
DATATYPES,,,
lat,xsd:decimal,,
lon,xsd:decimal,,
prmax,xsd:decimal,,
```


### Parsing Details

- Parsing and processing happen in independent stages, so the order of sections is not important
- Blank lines are ignored
- All contents are case-sensitive
- Cells beginning with `#` are ignored and can be used as comments
- Rows that start with `#` are ignored and can be used as comments


## How Annotation Works

### Initialization

Annotation begins by creating an `Annotation` object, whose constructor takes the file path of an annotation template as its only argument.

```{python}
anno = annotation.Annotation("sargasso-annotations.csv")
anno = annotation.Annotation("sargasso-annotations.csv", nrows=50)
```

During the initialization of the `Annotation` instance, a blank RDF graph (using Redland) and a variety of housekeeping variables related to parsing and processing the template file are set aside. At this point, the template file hasn't been parsed or processed in any way and there are no triples present in the graph.

### Parsing

The Parsing step reads the template file in, line-by-line, and does some pre-processing, and stores information for the Processing step.

Call the parsing method like:

```{python}
anno.parse()
```

Different types of work are done for each section:

#### META

The dataset specified in the `META` section under the key `data_identifier` is downloaded using `pandas::read_fwf` and saved to disk if the file is not already present in the working directory.
Note: This is not very flexible right now.


#### NAMESPACES

Namespace tuples are appending to a `Dict` for use during graph creation.


#### TRIPLES

Triples are immediately added to the graph.


#### OBSERVATIONS

Observations, Entities, and Contexts are immediately added to the graph and references to their RDF Nodes are saved for later use.


#### MAPPINGS

Mappings are parsed and saved for later.


#### DATATYPES

Datatypes are parsed and saved for later.


### Processing

The main method doing the work is the Processing step, called like:

```{python}
anno.process()
```

During the Processing step, mappings are read, one-by-one, and the corresponding data are retrieved from the dataset.
Using the information determined during the Parsing step, RDF nodes and triples for each value (cell) are created.


## Generating a Skeleton Template

Instead of creating an annotation template by hand, the user may want to create one by copying an existing template. As an alternative, `skeleton.py` creates an annotaton template based upon the structure of the data.
To generate a skeleton template, run the `skeleton.py` script on the command line, passing a filename to a dataset as the first and only argument.

Example:

```{bash}
python {path-to}/skeleton.py mydata.csv
```
