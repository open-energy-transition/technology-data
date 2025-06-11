"""Multi-purpose decorators."""

import functools
from typing import Any, Callable

import pandas as pd


def keep_unmodified_rows(id_columns: list[str], value_columns: list[str]) -> Callable:
    """
    Add a `keep_unmodified` parameter to a method.

    If `keep_unmodified=True` (default), unchanged rows from the original self.data
    are preserved in the result or re-added if necessary.
    If `keep_unmodified=False`, only modified rows remain.
    `id_columns` and `value_columns` are used to identify rows and values.

    Parameters
    ----------
    func : callable
        The method to be decorated.
    id_columns : list
        List of columns that uniquely identify rows.
    value_columns : list
        List of columns that contain the values to be compared.

    """

    def inner(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # Extract keep_unmodified parameter, default to True
            keep_unmodified = kwargs.pop("keep_unmodified", True)

            # Create a copy of the original data
            original_data: pd.DataFrame = self.data.copy()

            # Name and order of all columns as they will be returned later
            original_columns = original_data.columns

            # Call the original function
            result = func(self, *args, **kwargs)

            # Create a copy of the modified data
            modified_data: pd.DataFrame = self.data.copy()

            # Ensure that the id_columns and value_columns are in the data
            for col in id_columns + value_columns:
                if col not in original_data.columns or col not in modified_data.columns:
                    raise KeyError(
                        f"Column '{col}' must be present in both original and modified data to use this decorator."
                    )

            # Compare original and modified data
            if not original_data.empty and not modified_data.empty:
                # Merge original and modified data because they likely do not have the same index
                all_data: pd.DataFrame = original_data.merge(
                    modified_data,
                    how="outer",
                    on=id_columns,
                    suffixes=("_original", "_modified"),
                )

                # We assume that the index of the modified data is a subset of the original data
                # thus the merged data may have NaN values for the "_modified" columns which
                # we will fill with the original values.
                # The newly constructed value columns now contain all the information we need later
                # and get to have the names of the original value_columns.
                for col in value_columns:
                    all_data[col] = all_data[col + "_modified"].fillna(
                        all_data[col + "_original"]
                    )

                # Determine which rows have changed
                changed_mask = (
                    all_data[[col + "_original" for col in value_columns]].to_numpy()
                    != all_data[[col + "_modified" for col in value_columns]].to_numpy()
                ).any(axis=1)

                if keep_unmodified:
                    # Keep all, modified and unmodified, rows
                    self.data = all_data[original_columns]
                elif not keep_unmodified:
                    # Only keep modified rows
                    self.data = all_data.loc[changed_mask][original_columns]

                self.data = self.data.reset_index(drop=True)

            return result

        return wrapper

    return inner
