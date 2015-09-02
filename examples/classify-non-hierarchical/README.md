# Classification Examples (Non-Hierarchical)

(By non-hierarchical, I mean that the two classes we are trying to make equivalent are not subclasses of some super class.)

## Overview

We want to assert that two classes in separate measurement ontologies are the same (using the `OWL:equivalentClass` statement), we would like to explore the implications of these types of assertions.
Assertions of this type will be made in linking ontologies.
We want to know a number of things:

- Does a reasoner produces any errors for various ways of writing the linking ontology? (`reason.sh`)
- Can we make meaningful SPARQL queries across linked ontologies? (`query.sh`)

Similar to what has been done in [../classify_equivalentClasses](../classify_equivalentClasses), we have produced a set of test linking ontologies.
Ours are slightly modified but essentially the same with the main difference being that the linking ontologies in this directory do not user a super class.

The linking ontologies located in this directory are:

```{text}
├── test-equivclass-cardinality.owl
├── test-equivclass.owl
├── test-noequivclass-cardinality.owl
├── test-noequivclass.owl
```

All linking ontologies contain two classes (`A`, `B`), each class has a class-specific object property (`hasPropA`, `hasPropB`), and each class has one named individual. They differ with respect to whether they express `OWL:equivalentClass`  between class `A` and `B` and whether they assert a cardinality restriction on the number of object properties each class has (e.g. Instances of class `A` have exactly one and only property `PropA`.)
We then wrote a script that uses [OWLTools](https://github.com/owlcollab/owltools) to run the `HermiT 1.3.8` reasoner (which is an OWL 2 reasoner) over each linking ontology.

For the ontological reasoning step, each linking ontology was opened in [Protégé 4.3](http://protege.stanford.edu/) running the `HermiT 1.3.8` reasoner. Each linking ontolgoy was also run on the command line using [OWLTools](https://github.com/owlcollab/owltools) so the procedure could be reproduced.

## Results

To reproduce these results, you will need `sparql` and `owltools` in your `$PATH`.

### Reasoning

Corresponding command: `./reason.sh`

Result:

| Test Case | Filename | Consistent? |
|-----------|----------|-------------|
| 1 | test-noequivclass.owl | Yes |
| 2 | test-noequivclass-cardinality.owl | Yes |
| 3 | test-equivclass.owl | Yes |
| 4 | test-equivclass-cardinality.owl | Yes |

Raw output:

```{sh}
$ ./reason.sh
2015-09-02 09:17:59,362 INFO  (ParserWrapper:67) Start loading ontology: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-noequivclass.owl from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-noequivclass.owl
2015-09-02 09:17:59,480 INFO  (ParserWrapper:74) Finished loading ontology: null from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-noequivclass.owl
2015-09-02 09:17:59,551 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@bef2d72
all inferences
2015-09-02 09:17:59,553 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 09:17:59,557 INFO  (CommandRunner:2490) Iterating through all classes...
2015-09-02 09:17:59,563 INFO  (CommandRunnerBase:78) disposing of org.semanticweb.HermiT.Reasoner@bef2d72
2015-09-02 09:17:59,563 INFO  (CommandRunnerBase:70) disposing of org.semanticweb.HermiT.Reasoner@bef2d72
2015-09-02 09:17:59,968 INFO  (ParserWrapper:67) Start loading ontology: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-noequivclass-cardinality.owl from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-noequivclass-cardinality.owl
2015-09-02 09:18:00,095 INFO  (ParserWrapper:74) Finished loading ontology: null from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-noequivclass-cardinality.owl
2015-09-02 09:18:00,172 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@50b472aa
all inferences
2015-09-02 09:18:00,175 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 09:18:00,180 INFO  (CommandRunner:2490) Iterating through all classes...
INFERENCE: B 'B' EquivalentTo A 'A'
INFERENCE: A 'A' EquivalentTo B 'B'
2015-09-02 09:18:00,200 INFO  (CommandRunnerBase:78) disposing of org.semanticweb.HermiT.Reasoner@50b472aa
2015-09-02 09:18:00,200 INFO  (CommandRunnerBase:70) disposing of org.semanticweb.HermiT.Reasoner@50b472aa
2015-09-02 09:18:00,609 INFO  (ParserWrapper:67) Start loading ontology: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-equivclass.owl from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-equivclass.owl
2015-09-02 09:18:00,728 INFO  (ParserWrapper:74) Finished loading ontology: null from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-equivclass.owl
2015-09-02 09:18:00,802 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@a9cd3b1
all inferences
2015-09-02 09:18:00,805 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 09:18:00,808 INFO  (CommandRunner:2490) Iterating through all classes...
INFERENCE: B 'B' EquivalentTo A 'A'
INFERENCE: A 'A' EquivalentTo B 'B'
2015-09-02 09:18:00,823 INFO  (CommandRunnerBase:78) disposing of org.semanticweb.HermiT.Reasoner@a9cd3b1
2015-09-02 09:18:00,823 INFO  (CommandRunnerBase:70) disposing of org.semanticweb.HermiT.Reasoner@a9cd3b1
2015-09-02 09:18:01,232 INFO  (ParserWrapper:67) Start loading ontology: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-equivclass-cardinality.owl from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-equivclass-cardinality.owl
2015-09-02 09:18:01,362 INFO  (ParserWrapper:74) Finished loading ontology: null from: file:/Users/mecum/src/obs-models/examples/classify-non-hierarchical/./test-equivclass-cardinality.owl
2015-09-02 09:18:01,436 INFO  (CommandRunner:5529) Created reasoner: org.semanticweb.HermiT.Reasoner@50b472aa
all inferences
2015-09-02 09:18:01,439 INFO  (CommandRunner:2483) Checking for consistency...
Consistent? true
2015-09-02 09:18:01,443 INFO  (CommandRunner:2490) Iterating through all classes...
INFERENCE: B 'B' EquivalentTo A 'A'
INFERENCE: A 'A' EquivalentTo B 'B'
2015-09-02 09:18:01,459 INFO  (CommandRunnerBase:78) disposing of org.semanticweb.HermiT.Reasoner@50b472aa
2015-09-02 09:18:01,459 INFO  (CommandRunnerBase:70) disposing of org.semanticweb.HermiT.Reasoner@50b472aa
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
