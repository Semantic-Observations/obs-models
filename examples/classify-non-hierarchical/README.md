# Classification Examples (Non-Hierarchical)

(By non-hierarchical, I mean that the two classes we are trying to make equivalent are not subclasses of some super class.)

## Overview

We want to assert that two classes in separate measurement ontologies are the same (using the `OWL:equivalentClass` statement), we would like to explore the implications of these types of assertions.
Assertions of this type will be made in alignment ontologies.
We want to know a number of things:

- Does a reasoner produces any errors for various ways of writing the alignment ontology? (`reason.sh`)
- Does `OWL:equivalentClass` allow us to link two classes? (`reason.sh`)
- Can we make meaningful SPARQL queries across alignment ontologies? (`query.sh`)

Similar to what has been done in [../classify_equivalentClasses](../classify_equivalentClasses), we have produced a set of test alignment ontologies.
Ours are slightly modified but essentially the same with the main difference being that the alignment ontologies in this directory do not user a super class.

The alignment ontologies located in this directory are:

```{text}
├── test-equivclass-cardinality.owl
├── test-equivclass.owl
├── test-noequivclass-cardinality.owl
├── test-noequivclass.owl
```

All alignment ontologies contain two classes (`A`, `B`), each class has a class-specific object property (`hasPropA`, `hasPropB`), and each class has one named individual. They differ with respect to whether they express `OWL:equivalentClass`  between class `A` and `B` and whether they assert a cardinality restriction on the number of object properties each class has (e.g. Instances of class `A` have exactly one and only property `PropA`.)
We then wrote a script that uses [OWLTools](https://github.com/owlcollab/owltools) to run the `HermiT 1.3.8` reasoner (which is an OWL 2 reasoner) over each alignment ontology.

For the ontological reasoning step, each alignment ontology was opened in [Protégé 4.3](http://protege.stanford.edu/) running the `HermiT 1.3.8` reasoner. Each alignment ontolgoy was also run on the command line using [OWLTools](https://github.com/owlcollab/owltools) so the procedure could be reproduced.

## Results

To reproduce these results, you will need `sparql` and `owltools` in your `$PATH`.

### Reasoning

Corresponding command: `./reason.sh`

Result:

| Test Case | Filename                          | A::B | Consistent? |
|-----------|-----------------------------------|------|-------------|
| 1         | test-noequivclass.owl             | No   | Yes         |
| 2         | test-noequivclass-cardinality.owl | Yes  | Yes         |
| 3         | test-equivclass.owl               | Yes  | Yes         |
| 4         | test-equivclass-cardinality.owl   | Yes  | Yes         |

Abridged outputs:

`owltools ./test-noequivclass.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'`

```{sh}
2015-09-02 12:20:22,253 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@bef2d72
all inferences
2015-09-02 12:20:22,256 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 12:20:22,260 INFO  (CommandRunner:2490) Iterating through all classes...
# PARSING: A
Sep 02, 2015 12:20:22 PM org.obolibrary.macro.ManchesterSyntaxTool createParser
WARNING: parsing:A
# QUERY: A 'A'
E: A 'A'
D: owl:Nothing owl:Nothing
A:owl:Thing owl:Thing
```
`owltools ./test-noequivclass-cardinality.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'`


```{sh}
2015-09-02 12:20:22,923 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@50b472aa
all inferences
2015-09-02 12:20:22,926 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 12:20:22,931 INFO  (CommandRunner:2490) Iterating through all classes...
INFERENCE: B 'B' EquivalentTo A 'A'
INFERENCE: A 'A' EquivalentTo B 'B'
# PARSING: A
Sep 02, 2015 12:20:22 PM org.obolibrary.macro.ManchesterSyntaxTool createParser
WARNING: parsing:A
# QUERY: A 'A'
E: A 'A'
E: B 'B'
D: owl:Nothing owl:Nothing
A:owl:Thing owl:Thing
```

`owltools ./test-equivclass.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'`


```{sh}
2015-09-02 12:20:23,580 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@a9cd3b1
all inferences
2015-09-02 12:20:23,583 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 12:20:23,586 INFO  (CommandRunner:2490) Iterating through all classes...
INFERENCE: B 'B' EquivalentTo A 'A'
INFERENCE: A 'A' EquivalentTo B 'B'
# PARSING: A
Sep 02, 2015 12:20:23 PM org.obolibrary.macro.ManchesterSyntaxTool createParser
WARNING: parsing:A
# QUERY: A 'A'
E: A 'A'
E: B 'B'
D: owl:Nothing owl:Nothing
A:owl:Thing owl:Thing
```

`owltools ./test-equivclass-cardinality.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'`


```{sh}
2015-09-02 12:20:24,241 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@50b472aa
all inferences
2015-09-02 12:20:24,244 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 12:20:24,249 INFO  (CommandRunner:2490) Iterating through all classes...
INFERENCE: B 'B' EquivalentTo A 'A'
INFERENCE: A 'A' EquivalentTo B 'B'
# PARSING: A
Sep 02, 2015 12:20:24 PM org.obolibrary.macro.ManchesterSyntaxTool createParser
WARNING: parsing:A
# QUERY: A 'A'
E: A 'A'
E: B 'B'
D: owl:Nothing owl:Nothing
A:owl:Thing owl:Thing
```


## Querying

Corresponding command: `./query.sh`

Query 1: Find all individuals of type `A`.

Expect: Both INDIVI1 and INDIVI2

```{sparql}
select ?i where {
  ?i a obo:A
}
```

Result: Only INDIVI1, which is directly typed as being of class `A` is returned, no matter which ontology.

Raw output:

```{sh}
QUERY: query.rq

ONTOLOGY: test-equivclass-cardinality.owl
--------------
| i          |
==============
| obo:INDIV1 |
--------------
Time: 0.066 sec

ONTOLOGY: test-equivclass.owl
--------------
| i          |
==============
| obo:INDIV1 |
--------------
Time: 0.066 sec

ONTOLOGY: test-noequivclass-cardinality.owl
--------------
| i          |
==============
| obo:INDIV1 |
--------------
Time: 0.064 sec

ONTOLOGY: test-noequivclass.owl
--------------
| i          |
==============
| obo:INDIV1 |
--------------
Time: 0.062 sec
```

Query 2: Brute Force Query

```{sparql}
select ?i ?type where {
  ?i a/(rdfs:subClassOf|owl:equivalentClass|^owl:equivalentClass)* obo:A
}
```

Result: INDIV1 and INDIV2 are returned in every ontology where the `OWL:equivalentClass` statement is made.

The above SPARQL query isn't exactly what we want at this point as it uses what essentially amounts to a brute-force approach to find out whether INDIV1 is of type `A` and/or `B`.




```{sh}
QUERY: bruteforce.rq

ONTOLOGY: test-equivclass-cardinality.owl
---------------------
| i          | type |
=====================
| obo:INDIV1 |      |
| obo:INDIV2 |      |
---------------------
Time: 0.067 sec

ONTOLOGY: test-equivclass.owl
---------------------
| i          | type |
=====================
| obo:INDIV2 |      |
| obo:INDIV1 |      |
---------------------
Time: 0.075 sec

ONTOLOGY: test-noequivclass-cardinality.owl
---------------------
| i          | type |
=====================
| obo:INDIV1 |      |
| obo:INDIV2 |      |
---------------------
Time: 0.074 sec

ONTOLOGY: test-noequivclass.owl
---------------------
| i          | type |
=====================
| obo:INDIV1 |      |
---------------------
Time: 0.069 sec
```
