# tests/core/test_trail_insert_before.py

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


def test_insert_before_inserts_step_before_target_step():
    # Base pipeline: a -> c
    trail = Trail().then(a).then(c)

    # Insert b before c: a -> b -> c
    trail.insert_before("c", b)

    fp = OrderFootprint()
    trail.run(fp)

    assert fp.calls == ["a", "b", "c"], "insert_before() must place the inserted step immediately before the target step."
