
from unittest import mock

import rethink.source_reader
import rethink.specs
import rethink.known_specs


def test_load():
    rethink.known_specs.load(False,True)
    print(len(rethink.known_specs.known_specs))
    assert(False)
