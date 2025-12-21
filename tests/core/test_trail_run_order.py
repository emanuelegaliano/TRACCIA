# tests/core/test_trail_run_order.py

from traccia import FootprintMetadata, Trail, step


class OrderFootprint:
    def __init__(self):
        self.calls: list[str] = []
        self._metadata = FootprintMetadata()

    def get_metadata(self) -> FootprintMetadata:
        return self._metadata


@step()
def first(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("first")
    return fp


@step()
def second(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("second")
    return fp


def test_trail_runs_steps_in_order_and_returns_footprint():
    trail = Trail().then(first).then(second)
    fp = OrderFootprint()

    result = trail.run(fp)

    assert result is fp, "Trail.run() should return the resulting footprint (typically the same instance)."
    assert fp.calls == ["first", "second"], "Steps must run in the order they were added to the Trail."
