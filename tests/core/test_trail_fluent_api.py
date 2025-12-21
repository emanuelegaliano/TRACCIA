import pytest

from traccia import FootprintMetadata, Trail, step


class DummyFootprint:
    def __init__(self):
        self._metadata = FootprintMetadata()

    def get_metadata(self) -> FootprintMetadata:
        return self._metadata


@step()
def a(fp: DummyFootprint) -> DummyFootprint:
    return fp


@step()
def b(fp: DummyFootprint) -> DummyFootprint:
    return fp


def test_trail_methods_return_self_for_fluent_api():
    trail = Trail()

    returned = trail.then(a)
    assert returned is trail, "then() must return self for fluent chaining."

    returned = trail.replace("a", b)
    assert returned is trail, "replace() must return self for fluent chaining."

    returned = trail.remove("a")
    assert returned is trail, "remove() must return self for fluent chaining."

    returned = trail.insert_before("a", b)
    assert returned is trail, "insert_before() must return self for fluent chaining."

    # insert_after may not exist in all versions
    if hasattr(trail, "insert_after"):
        returned = trail.insert_after("a", b)
        assert returned is trail, "insert_after() must return self for fluent chaining."
    else:
        pytest.skip("Trail.insert_after() is not available in this version.")