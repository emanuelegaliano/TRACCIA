from dataclasses import dataclass, field
from typing import Any, Mapping
from pandas import DataFrame

from traccia.interfaces.footprint import FootprintMetadata
from ...interfaces import Footprint, Footstep


@dataclass
class DataMiningFootprint(Footprint):
    """
    Generic payload for data-mining pipelines.

    For the PreProcessor path we mainly use:
    - raw_df:         original dataframe as loaded from source
    - cleaned_df:     working dataframe after preprocessing steps
    - schema:         expected / inferred schema (column -> dtype/info)
    - preprocessing_log: human-readable log of what has been done
    """

    # Original dataset (never modified by preprocessing steps)
    raw_df: DataFrame

    # Working copy, progressively modified by preprocessing steps
    cleaned_df: DataFrame | None = None

    # Optional schema information, e.g. {"date": "datetime64[ns]", "amount": "float"}
    schema: dict[str, Any] = field(default_factory=dict)

    # Human-readable log of preprocessing operations
    preprocessing_log: list[str] = field(default_factory=list)

    # Free container for additional info/artifacts
    artifacts: dict[str, Any] = field(default_factory=dict)

    # Internal metadata object shared across the whole pipeline
    _metadata: FootprintMetadata = field(
        default_factory=FootprintMetadata,
        repr=False,
    )

    def get_metadata(self) -> FootprintMetadata:
        """
        Return the FootprintMetadata associated with this footprint.

        The same metadata instance is reused for the lifetime of the
        DataMiningFootprint, so footsteps and tooling can safely
        mutate it (add handlers, tags, timestamps, etc.).
        """
        return self._metadata


@dataclass
class VariableCleaningFootstep(Footstep):
    """
    Generic step for variable cleaning:
    - column renaming
    - type casting with optional strict checks
    """

    rename_map: Mapping[str, str] | None = None
    expected_dtypes: Mapping[str, Any] | None = None
    strict: bool = True

    # 👇 Questo è il metodo richiesto dall'interfaccia Footstep
    def execute(self, footprint: Footprint) -> Footprint:
        """
        Entry point required by TRACCIA's Footstep interface.

        It expects a DataMiningFootprint; if a different footprint
        type is passed, a TypeError is raised.
        """
        if not isinstance(footprint, DataMiningFootprint):
            raise TypeError(
                f"{self.__class__.__name__} expects a DataMiningFootprint, "
                f"got {type(footprint)!r}."
            )

        fp: DataMiningFootprint = footprint

        # 1. Decide which dataframe to work on
        if fp.cleaned_df is None:
            df = fp.raw_df.copy()
            fp.preprocessing_log.append("Initialized cleaned_df from raw_df.")
        else:
            df = fp.cleaned_df.copy()

        # 2. Column renaming
        if self.rename_map:
            missing_for_rename = [col for col in self.rename_map.keys() if col not in df.columns]
            if missing_for_rename:
                msg = (
                    "VariableCleaningFootstep: columns not found for renaming: "
                    f"{missing_for_rename}"
                )
                if self.strict:
                    raise ValueError(msg)
                fp.preprocessing_log.append(msg)
            # Rename only existing columns
            rename_effective = {old: new for old, new in self.rename_map.items() if old in df.columns}
            if rename_effective:
                df = df.rename(columns=rename_effective)
                fp.preprocessing_log.append(f"Renamed columns: {rename_effective}")

        # 3. Type casting
        if self.expected_dtypes:
            for col, dtype in self.expected_dtypes.items():
                if col not in df.columns:
                    msg = f"VariableCleaningFootstep: column '{col}' not found for type casting."
                    if self.strict:
                        raise ValueError(msg)
                    fp.preprocessing_log.append(msg)
                    continue

                try:
                    df[col] = df[col].astype(dtype)
                    fp.preprocessing_log.append(f"Casted column '{col}' to dtype '{dtype}'.")
                    # Update schema
                    fp.schema[col] = str(df[col].dtype)
                except Exception as exc:  # noqa: BLE001
                    msg = (
                        "VariableCleaningFootstep: failed to cast "
                        f"column '{col}' to '{dtype}': {exc}"
                    )
                    if self.strict:
                        raise ValueError(msg) from exc
                    fp.preprocessing_log.append(msg)

        # 4. Save back into the footprint
        fp.cleaned_df = df

        # (Facoltativo) tracciare il passaggio nel metadata
        fp.get_metadata().add_handler(self.__class__.__name__)

        return fp

    # 👇 Facoltativo: comodo se vuoi continuare a usare `run(...)` nel tuo codice
    def run(self, footprint: DataMiningFootprint) -> DataMiningFootprint:
        """
        Convenience wrapper around `execute` with a more specific type.
        """
        result = self.execute(footprint)
        # type checker non sa che result è DataMiningFootprint, quindi fai un cast o un semplice return
        return result  # type: ignore[return-value]