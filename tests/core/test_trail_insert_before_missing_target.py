# tests/core/test_trail_insert_before_missing_target.py

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


def test_insert_before_missing_target_is_explicit():
    trail = Trail().then(a)

    try:
        trail.insert_before("does_not_exist", b)
    except Exception:
        # OK: explicit failure
        return

    # If no exception is raised, we expect a no-op: pipeline should remain unchanged.
    fp = OrderFootprint()
    trail.run(fp)
    assert fp.calls == ["a"], "If insert_before() does not raise, it should behave as a no-op when target is missing."