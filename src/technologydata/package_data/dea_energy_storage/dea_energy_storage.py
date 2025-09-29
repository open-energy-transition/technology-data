# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Data parser for the DEA energy storage data set."""

import pathlib
import re

import pandas

path_cwd = pathlib.Path.cwd()


def get_conversion_dictionary() -> dict[str, str]:
    """
    Provide conversion dictionary between data source column names and TechnologyCollection attribute names.

    Returns
    -------
    Dictionary
        conversion dictionary that renames columns to TechnologyCollection attribute names.

    """
    return {
        "Technology": "name",
        "par": "parameters",
        "Variable O&M": "VOM",
        "Fuel": "fuel",
        "Additional OCC": "investment",
        "WACC Real": "discount rate",
    }


def clean_parameter_string(text_string: str) -> str:
    """
    Remove any string between square brackets and any leading hyphen or double quotes from the input string.

    Parameters
    ----------
    text_string : str
        input string to be cleaned.

    Returns
    -------
    str
        cleaned string with square brackets and leading hyphen or double quotes removed.

    """
    # Remove leading hyphen
    text_string = text_string.lstrip("-")

    # Remove content inside brackets including the brackets themselves
    result = re.sub(r"\[.*?\]", "", text_string)

    # Remove extra spaces resulting from the removal
    result = re.sub(r"\s+", " ", result).strip()

    return result


if __name__ == "__main__":
    # Read the raw data
    dea_energy_storage_file_path = pathlib.Path(
        path_cwd,
        "src",
        "technologydata",
        "package_data",
        "raw",
        "Technology_datasheet_for_energy_storage.xlsx",
    )
    dea_energy_storage_df = pandas.read_excel(
        dea_energy_storage_file_path, sheet_name="alldata_flat"
    )

    # Clean parameter column
    dea_energy_storage_df["par"] = dea_energy_storage_df["par"].apply(
        clean_parameter_string
    )
