from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd
from pandas import DataFrame

from ...interfaces.footprint import FootprintMetadata, Footprint as FootprintProtocol
from ...interfaces.footstep import Footstep
from ...core.path import Path


# ---------------------------------------------------------------------------
# Footprint
# ---------------------------------------------------------------------------


@dataclass
class DataMiningFootprint(FootprintProtocol):
    """
    Generic payload for data-mining pipelines.

    For the PreProcessor path we mainly use:
    - raw_df:         original dataframe as loaded from source
    - cleaned_df:     working dataframe after preprocessing steps
    - schema:         expected / inferred schema (column -> dtype/info)
    - preprocessing_log: human-readable log of what has been done
    """

    raw_df: DataFrame
    cleaned_df: DataFrame | None = None
    schema: dict[str, Any] = field(default_factory=dict)
    preprocessing_log: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    _metadata: FootprintMetadata = field(
        default_factory=FootprintMetadata,
        repr=False,
    )

    def get_metadata(self) -> FootprintMetadata:
        """
        Return the FootprintMetadata associated with this footprint.
        """
        return self._metadata


# ---------------------------------------------------------------------------
# Footstep 1: VariableCleaningFootstep
# ---------------------------------------------------------------------------


@dataclass
class VariableCleaningFootstep(Footstep[DataMiningFootprint]):
    """
    Generic step for variable cleaning:
    - column renaming
    - type casting with optional strict checks

    Parameters
    ----------
    rename_map:
        Mapping from old column names to new column names.
        Columns not included remain unchanged.

    expected_dtypes:
        Mapping from column names (after renaming) to expected dtypes.
        Each value can be a Python type (e.g., float, int, str)
        or a pandas dtype string (e.g., 'float64', 'int64', 'datetime64[ns]').

    strict:
        If True:
            - raise ValueError when a specified column is missing
            - raise ValueError when a cast fails
        If False:
            - log the issue in the footprint and keep going
    """

    rename_map: Mapping[str, str] | None = None
    expected_dtypes: Mapping[str, Any] | None = None
    strict: bool = True

    def __post_init__(self) -> None:
        # Initialize Footstep internals (_name, _next_footstep, etc.)
        super().__init__()

    def run(self, footprint: DataMiningFootprint) -> DataMiningFootprint:
        # 1. Decide which dataframe to work on
        if footprint.cleaned_df is None:
            df = footprint.raw_df.copy()
            footprint.preprocessing_log.append("VariableCleaningFootstep: initialized cleaned_df from raw_df.")
        else:
            df = footprint.cleaned_df.copy()

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
                footprint.preprocessing_log.append(msg)

            rename_effective = {old: new for old, new in self.rename_map.items() if old in df.columns}
            if rename_effective:
                df = df.rename(columns=rename_effective)
                footprint.preprocessing_log.append(f"VariableCleaningFootstep: renamed columns {rename_effective}.")

        # 3. Type casting
        if self.expected_dtypes:
            for col, dtype in self.expected_dtypes.items():
                if col not in df.columns:
                    msg = f"VariableCleaningFootstep: column '{col}' not found for type casting."
                    if self.strict:
                        raise ValueError(msg)
                    footprint.preprocessing_log.append(msg)
                    continue

                try:
                    df[col] = df[col].astype(dtype)
                    footprint.preprocessing_log.append(
                        f"VariableCleaningFootstep: casted column '{col}' to dtype '{dtype}'."
                    )
                    footprint.schema[col] = str(df[col].dtype)
                except Exception as exc:  # noqa: BLE001
                    msg = (
                        f"VariableCleaningFootstep: failed to cast column "
                        f"'{col}' to '{dtype}': {exc}"
                    )
                    if self.strict:
                        raise ValueError(msg) from exc
                    footprint.preprocessing_log.append(msg)

        footprint.cleaned_df = df

        # Delegate to the next Footstep in the chain (if any)
        return super().run(footprint)


# ---------------------------------------------------------------------------
# Footstep 2: MissingValuesFootstep
# ---------------------------------------------------------------------------


@dataclass
class MissingValuesFootstep(Footstep[DataMiningFootprint]):
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

    def __post_init__(self) -> None:
        # Initialize Footstep internals (_name, _next_footstep, etc.)
        super().__init__()

    def run(self, footprint: DataMiningFootprint) -> DataMiningFootprint:
        fp = footprint

        # 1. Choose dataframe to work on
        if fp.cleaned_df is None:
            df = fp.raw_df.copy()
            fp.preprocessing_log.append(
                "MissingValuesFootstep: initialized cleaned_df from raw_df."
            )
        else:
            df = fp.cleaned_df.copy()

        # 2. Apply strategies column by column
        for col, strategy in self.column_strategies.items():
            if col not in df.columns:
                msg = f"MissingValuesFootstep: column '{col}' not found."
                if self.strict:
                    raise ValueError(msg)
                fp.preprocessing_log.append(msg)
                continue

            n_missing = df[col].isna().sum()
            if n_missing == 0:
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: no missing values in column '{col}'."
                )
                continue

            strategy_norm = strategy.lower().strip()

            if strategy_norm == "drop_rows":
                before = len(df)
                df = df[df[col].notna()]
                after = len(df)
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: dropped {before - after} rows due to NaNs in '{col}'."
                )

            elif strategy_norm in {"mean", "median"}:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    msg = (
                        f"MissingValuesFootstep: strategy '{strategy_norm}' "
                        f"requires numeric dtype for column '{col}'."
                    )
                    if self.strict:
                        raise ValueError(msg)
                    fp.preprocessing_log.append(msg)
                    continue

                if strategy_norm == "mean":
                    fill_value = df[col].mean()
                else:
                    fill_value = df[col].median()

                df[col] = df[col].fillna(fill_value)
                fp.preprocessing_log.append(
                    f"MissingValuesFootstep: filled {n_missing} NaNs in '{col}' "
                    f"using {strategy_norm}={fill_value}."
                )

            elif strategy_norm == "mode":
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

            elif strategy_norm == "constant":
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
                    f"MissingValuesFootstep: unsupported strategy '{strategy_norm}' "
                    f"for column '{col}'."
                )
                if self.strict:
                    raise ValueError(msg)
                fp.preprocessing_log.append(msg)
                continue

        fp.cleaned_df = df

        # Delegate to the next Footstep in the chain (if any)
        return super().run(fp)


# ---------------------------------------------------------------------------
# Path: PreprocessingPath
# ---------------------------------------------------------------------------


class PreprocessingPath(Path[DataMiningFootprint]):
    """
    Simple TRACCIA Path that runs all preprocessing footsteps in sequence
    on a DataMiningFootprint.
    """

    def __init__(
        self,
        cleaning_step: VariableCleaningFootstep,
        missing_step: MissingValuesFootstep,
        run_id: str | None = None,
    ) -> None:
        super().__init__(
            cleaning_step,
            missing_step,
            name="PreprocessingPath",
            run_id=run_id,
        )