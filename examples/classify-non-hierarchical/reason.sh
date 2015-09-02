#!/bin/sh

owltools ./test-noequivclass.owl --reasoner hermit --run-reasoner
owltools ./test-noequivclass-cardinality.owl --reasoner hermit --run-reasoner
owltools ./test-equivclass.owl --reasoner hermit --run-reasoner
owltools ./test-equivclass-cardinality.owl --reasoner hermit --run-reasoner
