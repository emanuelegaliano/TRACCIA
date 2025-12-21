# tests/core/test_step_callable_object.py

from traccia import FootprintMetadata, Step


class DummyFootprint:
    def __init__(self):
        self.value = 0
        self._metadata = FootprintMetadata()

    def get_metadata(self) -> FootprintMetadata:
        return self._metadata


class AddN:
    def __init__(self, n: int):
        self.n = n

    def __call__(self, fp: DummyFootprint) -> DummyFootprint:
        fp.value += self.n
        return fp


def test_step_wraps_callable_object_and_is_callable():
    add5 = Step(name="add_5", fn=AddN(5))

    fp = DummyFootprint()
    out = add5(fp)

    assert out is fp
    assert fp.value == 5
    assert getattr(add5, "name", None) == "add_5"
