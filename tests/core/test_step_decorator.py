# tests/core/test_step_decorator.py

from traccia import FootprintMetadata, step


class DummyFootprint:
    def __init__(self):
        self.value = 0
        self._metadata = FootprintMetadata()

    def get_metadata(self) -> FootprintMetadata:
        return self._metadata


def test_step_decorator_preserves_function_name_as_step_name():
    @step()
    def increment(fp: DummyFootprint) -> DummyFootprint:
        fp.value += 1
        return fp

    # Most libraries set Step.name = function.__name__
    # We test the contract used by Trail methods that take step_name: str.
    assert getattr(increment, "name", None) == "increment", (
        "The @step() decorator should produce a Step with a stable 'name' "
        "derived from the original function name."
    )


def test_step_is_callable_and_executes_wrapped_function():
    @step()
    def increment(fp: DummyFootprint) -> DummyFootprint:
        fp.value += 1
        return fp

    fp = DummyFootprint()
    out = increment(fp)

    assert out is fp
    assert fp.value == 1