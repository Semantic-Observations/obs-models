import pytest
from csvtotriples import annotation


def test_unionof():
    anno = annotation.Annotation("tests/test_templates/test_bnode_support.csv")
    anno.parse()
    anno.process()

    assert(anno.size() == 2)
