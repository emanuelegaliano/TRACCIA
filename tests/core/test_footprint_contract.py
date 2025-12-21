# tests/core/test_footprint_contract.py

from traccia import FootprintMetadata


class DummyFootprint:
    def __init__(self):
        self._metadata = FootprintMetadata()

    def get_metadata(self) -> FootprintMetadata:
        return self._metadata


def test_footprint_metadata_is_stable_instance():
    fp = DummyFootprint()

    m1 = fp.get_metadata()
    m2 = fp.get_metadata()

    assert m1 is m2, "get_metadata() must always return the same FootprintMetadata instance"
