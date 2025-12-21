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


def test_remove_removes_first_matching_step():
    # a -> b -> c -> b
    trail = Trail().then(a).then(b).then(c).then(b)

    trail.remove("b")

    fp = OrderFootprint()
    trail.run(fp)

    # only the FIRST "b" is removed
    assert fp.calls == ["a", "c", "b"], (
        "remove() must remove only the first matching step."
    )


def test_remove_is_noop_when_step_not_found():
    trail = Trail().then(a).then(c)

    trail.remove("does_not_exist")

    fp = OrderFootprint()
    trail.run(fp)

    assert fp.calls == ["a", "c"], (
        "remove() must be a no-op when the target step is not found."
    )