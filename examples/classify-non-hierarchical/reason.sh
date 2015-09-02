#!/bin/sh

owltools ./test-noequivclass.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'
owltools ./test-noequivclass-cardinality.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'
owltools ./test-equivclass.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'
owltools ./test-equivclass-cardinality.owl --reasoner hermit --run-reasoner --assert-implied --reasoner-query 'A'
