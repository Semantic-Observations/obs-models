# CSV To Triples

`csvtotriples` automatically generate triples for a dataset according to an observations ontology.
For now, the annotation script and template only work with the OBOE ontology but wouldn't require significant modification to work with others.

This work can be done by hand but is tedious and time-consuming for larger datasets and the work is highly redundant. By using a template to describe the set of triples we wish to generate, this work becomes more efficient and potentially less error-prone.

The script `annotate.py` reads in an annotation template file (CSV format) and produces and
semantic observations graph for the data inside a CSV file.
The script `csvtotriples/skeleton.py` generates an empty (skeleton) annotation template and is a good place to start when creating an annotation template for a new dataset.

## Template File

The template file format was designed to make it easy to annotate a dataset with minimal repetition.

The file contains six sections which contain specific information relevant to the automatic annotation process:

- META: Identifiers for the metadata (optional) and data. [required]
- NAMESPACES: Namespaces for the annotation graph. [optional]
- TRIPLES: Triples the user wants to manually specify. These are simply added directly to the graph. [optional]
- OBSERVATIONS: The observations the data are being annotated with. [required]
- MAPPINGS: Mappings between a semantic concept and attributes of the data [required]
- DATATYPES: Datatype for attributes (columns) of the data [optional]

Each section may contain a number of values:

### META:

`metadata_identifier`: URI for the dataset's metadata

`data_identifier`: URI for the data itself. This URI should be resolvable and return the dataset.

Example:

```{csv}
META,,,
metadata_identifier,http://www.bco-dmo.org/dataset/3584,,
data_identifier,http://data.bco-dmo.org/jg/serv/BCO/vanMooy/SargassoSeaLipids/X1103_CTD_profiles.flat9,,
```


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


### OBSERVATIONS

This section contains a hierarchical description of OBOE Observations, Entities, Measurements, Characteristics, Standards, and Contexts.
Blank cells are used to encode the hierarchy.

```
observation , o1          ,                ,
            , entity      , e1             , foo:myentity
            , measurement , m1             ,
            ,             , characteristic , foo:mycharacteristic
            ,             , standard       , foo:mystandard
            , context     , o2             ,

```

In the above code block, an Observation with key `o1` is of an Entity `e1`, has a Measurement `m1`, and a Context of Observation `o2`. The keys uniquely specify linkages between instances of concepts within the template.
In the above example, a lower case letter matching the first letter of the corresponding to a semantic concept (i.e. o for Observation)  is followed by a number but this is just used for clarity and the only requirement is that keys must be non-zero-length strings.
Moving one level of indentation (column) over to the right, the above code block specifies that Measurement `m1` is of a Characteristic `foo:mycharacteristic` and was measured according to Standard `foo:mystandard`.
In the previous sentence, short-hand URIs are used instead of keys.
This is because no within-document linkages are made for Characteristics and Standards.

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
`attribute,key,value,condition`

For the first form, attributes (usually columns) of the data are mapped onto a semantic concept by its key (usually a measurement, e.g. m1).
For the second form, attributes are again mapped to semantic concepts but instead of the values being read from the data and inserted directly into the graph, as in the tuple form, the `value` is substituted from the mapping according to a condition.

For example, say you had data with the column `spp` which contained the species being measured. If the triples you wanted to generate were:

```{ttl}
[]
    oboe:hasValue "Oncorhynchus tshawytscha" ;
    a oboe:Measurement .
```

but the data had encoded the species using a common name, such as "King", we could handle this with the following mapping:

`spp,m3,Oncorhynchus tshawytscha,spp eq Chinook`

Example:

```{csv}
MAPPINGS,,,
cast,m1,,
date,m2,,
time,m3,,
```

Without a mapping covering values within the data, values from the data won't be entered into the graph.
Mappings select data from a column of the dataset and add the necessary triples for that value to the graph.
If no mappings are specified, no Measurements/Characteristics/Standards will be added to the graph (and no values either)
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
- Text beginning with `#` are ignored and can be used as comments


## How Annotation Works

### Initialization

Annotation begins by creating an `Annotation` object, whose constructor takes the file path of an annotation template as its only argument.

```{python}
anno = annotation.Annotation("sargasso-annotations.csv")
```

During the initialization of the `Annotation` instance, a blank RDF graph (using Redland) and a variety of housekeeping variables related to parsing and processing the template file are set aside. At this point, the template file hasn't been parsed or processed in any way and there are no triples present in the graph.


### Processing

The main method doing the work is the `process` method on the instance of the `Annotation` class:

```{python}
anno.process()
```

Once called, the template file is read, line-by-line, and each section is processed immediately. This has different meaning for each section:

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


## Generating a Skeleton Template

Note: This script is in progress.

Instead of creating an annotation template by hand, the user may want to create one by copying an existing template. As an alternative, `skeleton.py` creates an annotaton template based upon the structure of the data.
To generate a skeleton template, run the `skeleton.py` script on the command line, passing a filename to a dataset as the first and only argument.

Example:

```{bash}
python {path-to}/skeleton.py mydata.csv
```
