from dataclasses import dataclass, field
from typing import Any, Mapping
import pandas as pd
from pandas import DataFrame

from ...interfaces.footprint import FootprintMetadata
from ...interfaces import Footprint, Footstep
from ...core.path import Path


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
    

@dataclass
class MissingValuesFootstep(Footstep):
    """
    Generic step for handling missing values.

    The behaviour is configured per-column via `column_strategies`.

    Parameters
    ----------
    column_strategies:
        Mapping from column name to strategy name.
        Supported strategies:
            - "drop_rows": drop rows where this column is null
            - "mean":      fill nulls with column mean   (numeric)
            - "median":    fill nulls with column median (numeric)
            - "mode":      fill nulls with column mode   (first mode)
            - "constant":  fill nulls with a constant value (see `constant_values`)

    constant_values:
        Optional mapping from column name to the value to be used when
        strategy == "constant". If a column is configured with
        "constant" but not found in `constant_values`, behaviour
        depends on `strict`.

    strict:
        If True:
            - raise ValueError when a specified column is missing
            - raise ValueError when a strategy is invalid or cannot be applied
        If False:
            - log a message in the footprint and continue
    """

    column_strategies: Mapping[str, str]
    constant_values: Mapping[str, Any] | None = None
    strict: bool = True

    def execute(self, footprint: Footprint) -> Footprint:
        if not isinstance(footprint, DataMiningFootprint):
            raise TypeError(
                f"{self.__class__.__name__} expects a DataMiningFootprint, "
                f"got {type(footprint)!r}."
            )

        fp: DataMiningFootprint = footprint

        # 1. Scegli il dataframe su cui lavorare
        if fp.cleaned_df is None:
            df = fp.raw_df.copy()
            fp.preprocessing_log.append(
                "MissingValuesFootstep: initialized cleaned_df from raw_df."
            )
        else:
            df = fp.cleaned_df.copy()

        # 2. Applica le strategie colonna per colonna
        for col, strategy in self.column_strategies.items():
            if col not in df.columns:
                msg = f"MissingValuesFootstep: column '{col}' not found."
                if self.strict:
                    raise ValueError(msg)
                fp.preprocessing_log.append(msg)
                continue

            # Se non ci sono NaN, non facciamo nulla (ma lo logghiamo)
            n_missing = df[col].isna().sum()
            if n_missing == 0:
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: no missing values in column '{col}'."
                )
                continue

            strategy = strategy.lower().strip()

            if strategy == "drop_rows":
                before = len(df)
                df = df[df[col].notna()]
                after = len(df)
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: dropped {before - after} rows due to NaNs in '{col}'."
                )

            elif strategy in {"mean", "median"}:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    msg = (
                        f"MissingValuesFootstep: strategy '{strategy}' "
                        f"requires numeric dtype for column '{col}'."
                    )
                    if self.strict:
                        raise ValueError(msg)
                    fp.preprocessing_log.append(msg)
                    continue

                if strategy == "mean":
                    fill_value = df[col].mean()
                else:  # median
                    fill_value = df[col].median()

                df[col] = df[col].fillna(fill_value)
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: filled {n_missing} NaNs in '{col}' "
                    f"using {strategy}={fill_value}."
                )

            elif strategy == "mode":
                mode_series = df[col].mode(dropna=True)
                if mode_series.empty:
                    msg = (
                        f"MissingValuesFootstep: cannot compute mode for column '{col}' "
                        "(no non-null values)."
                    )
                    if self.strict:
                        raise ValueError(msg)
                    fp.preprocessing_log.append(msg)
                    continue

                fill_value = mode_series.iloc[0]
                df[col] = df[col].fillna(fill_value)
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: filled {n_missing} NaNs in '{col}' "
                    f"using mode={fill_value!r}."
                )

            elif strategy == "constant":
                if not self.constant_values or col not in self.constant_values:
                    msg = (
                        f"MissingValuesFootstep: strategy 'constant' for column '{col}' "
                        "but no value provided in `constant_values`."
                    )
                    if self.strict:
                        raise ValueError(msg)
                    fp.preprocessing_log.append(msg)
                    continue

                fill_value = self.constant_values[col]
                df[col] = df[col].fillna(fill_value)
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: filled {n_missing} NaNs in '{col}' "
                    f"using constant={fill_value!r}."
                )

            else:
                msg = (
                    f"MissingValuesFootstep: unsupported strategy '{strategy}' "
                    f"for column '{col}'."
                )
                if self.strict:
                    raise ValueError(msg)
                fp.preprocessing_log.append(msg)
                continue

        # 3. Salva il dataframe aggiornato nel footprint
        fp.cleaned_df = df

        # 4. Registra il passaggio nel metadata
        fp.get_metadata().add_handler(self.__class__.__name__)

        return fp

    # Facoltativo, come per il Footstep precedente
    def run(self, footprint: DataMiningFootprint) -> DataMiningFootprint:
        result = self.execute(footprint)
        return result  # type: ignore[return-value]



class PreprocessingPath(Path[DataMiningFootprint]):
    """
    Simple TRACCIA Path that runs all preprocessing footsteps in sequence
    on a DataMiningFootprint.

    The internal Path wiring uses a Chain of Responsibility:
      - only the first Footstep is triggered by `run(...)`;
      - each Footstep is responsible for delegating to the next one.
    """

    def __init__(
        self,
        cleaning_step: VariableCleaningFootstep,
        missing_step: MissingValuesFootstep,
        run_id: str | None = None,
    ) -> None:
        # Pass footsteps as varargs, and optionally set a name + run_id
        super().__init__(
            cleaning_step,
            missing_step,
            name="PreprocessingPath",
            run_id=run_id,
        )