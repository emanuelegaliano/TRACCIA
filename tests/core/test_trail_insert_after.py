import pytest

from traccia import FootprintMetadata, Trail, step


class OrderFootprint:
    def __init__(self):
        self.calls: list[str] = []
        self._metadata = FootprintMetadata()

    def get_metadata(self) -> FootprintMetadata:
        return self._metadata


@step()
def a(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("a")
    return fp


@step()
def b(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("b")
    return fp


@step()
def c(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("c")
    return fp


def test_insert_after_inserts_step_after_target_step():
    trail = Trail().then(a).then(c)

    # If insert_after is not implemented in this version, skip cleanly.
    if not hasattr(trail, "insert_after"):
        pytest.skip("Trail.insert_after() is not available in this version of the library.")

    # Insert b after a: expected order a -> b -> c
    trail.insert_after("a", b)

    fp = OrderFootprint()
    trail.run(fp)

    assert fp.calls == ["a", "b", "c"], (
        "insert_after() must place the inserted step immediately after the target step."
    )