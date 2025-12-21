# tests/core/test_trail_replace.py

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


@step()
def x(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("x")
    return fp


@step()
def y(fp: OrderFootprint) -> OrderFootprint:
    fp.calls.append("y")
    return fp


def test_replace_replaces_first_matching_step_with_multiple_steps():
    # Pipeline with duplicate step name "b" to ensure ONLY the first one is replaced.
    trail = Trail().then(a).then(b).then(c).then(b)

    # Replace first "b" with x, y
    returned = trail.replace("b", x, y)

    # Fluent API: should return self
    assert returned is trail

    fp = OrderFootprint()
    trail.run(fp)

    # Expected: a -> x -> y -> c -> b
    assert fp.calls == ["a", "x", "y", "c", "b"], (
        "replace() must replace only the first matching step and insert new steps in order."
    )


def test_replace_is_noop_when_step_name_not_found():
    trail = Trail().then(a).then(c)
    trail.replace("does_not_exist", x)

    fp = OrderFootprint()
    trail.run(fp)

    assert fp.calls == ["a", "c"], "replace() must be a no-op when the target step name is not found."


def test_replace_is_noop_when_no_new_steps_provided():
    trail = Trail().then(a).then(b).then(c)
    trail.replace("b")  # no new steps

    fp = OrderFootprint()
    trail.run(fp)

    assert fp.calls == ["a", "b", "c"], "replace() must be a no-op when no replacement steps are provided."