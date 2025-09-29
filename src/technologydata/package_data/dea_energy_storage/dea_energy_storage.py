# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Data parser for the DEA energy storage data set."""
import logging
import pathlib
import re

import pandas

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


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


def drop_invalid_rows(dataframe: pandas.DataFrame) -> pandas.DataFrame:
    """
    Remove rows from the DataFrame where certain columns contain invalid data.

    This function drops rows where:
    - The 'Technology' or 'par' columns are None or empty strings (including strings with only whitespace).
    - The 'year' column does not contain any digits.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        The input DataFrame to be cleaned.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame with rows containing invalid data removed.

    """
    # Drop rows where 'technology' or 'par' are None or empty strings
    df_cleaned = dataframe.dropna(subset=["Technology", "par"])
    df_cleaned = df_cleaned[~df_cleaned["Technology"].astype(str).str.strip().eq("")]
    df_cleaned = df_cleaned[~df_cleaned["par"].astype(str).str.strip().eq("")]

    # Drop rows where 'year' does not contain any digit
    df_cleaned = df_cleaned[df_cleaned["year"].astype(str).str.contains(r"\d")]

    return df_cleaned


def clean_parameter_string(text_string: str) -> str:
    """
    Remove any string between square brackets and any leading hyphen or double quotes from the input string. Lower-case all.

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

    # Remove extra spaces resulting from the removal and set all to lower case
    result = re.sub(r"\s+", " ", result).strip().casefold()

    return result


def clean_technology_string(tech_str: str) -> str:
    """
    Safely clean a technology string by converting it to lowercase and stripping whitespace.

    This function attempts to convert the input to a string, apply case folding for
    case-insensitive comparisons, and remove leading/trailing whitespace. If an exception
    occurs during this process, it catches the exception, prints an error message, and
    returns the original input.

    Parameters
    ----------
    tech_str : any
        The input value representing a technology string, which may not be a string.

    Returns
    -------
    str
        The cleaned technology string if conversion is successful; otherwise, returns
        the original input.

    """
    try:
        return str(tech_str).casefold().strip()
    except Exception as e:
        logger.error(f"Error cleaning technology '{tech_str}': {e}")
        return tech_str


def safe_extract_year(year_str: str | int | float | None) -> int | None:
    """
    Safely extract the first year (integer) from a given input.

    Parameters
    ----------
    year_str : str or int or float or None
        Input value containing a potential year.
        Can be a string with embedded year, a numeric value, or None.

    Returns
    -------
    int or None
        Extracted first year as an integer.
        Returns None (pandas.NA) if no year is found or input is invalid.

    Raises
    ------
    TypeError
        If input cannot be converted to string.

    Examples
    --------
    >>> safe_extract_year('uncertainty (2050)')
    2050
    >>> safe_extract_year('some text 2025 more text')
    2025
    >>> safe_extract_year(None)
    None
    >>> safe_extract_year('no year here')
    None

    Notes
    -----
    - Handles various input formats
    - Extracts first set of digits found in the input
    - Uses regex to find years
    - Robust against different input types

    """
    try:
        # Handle various input types
        if pandas.isna(year_str):
            return None

        # Convert to string
        year_str = str(year_str)

        # Extract first set of digits
        digits = re.findall(r"\d+", year_str)

        # Convert to integer
        return int(digits[0]) if digits else None
    except Exception as e:
        logger.error(f"Error extracting year from '{year_str}': {e}")
        return None


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

    # Drop unnecessary rows
    cleaned_df = drop_invalid_rows(dea_energy_storage_df)

    # Clean parameter (par) column
    dea_energy_storage_df["par"] = dea_energy_storage_df["par"].apply(
        clean_parameter_string
    )

    # Clean technology (Technology) column
    dea_energy_storage_df["Technology"] = dea_energy_storage_df["Technology"].apply(
        clean_technology_string
    )




    dea_energy_storage_df["year"] = dea_energy_storage_df["year"].apply(
        safe_extract_year
    )

    # Get unique values of technology-year pair
    unique_year = (
        dea_energy_storage_df["year"]
        .dropna()
        .astype(str)
        .str.casefold()
        .str.strip()
        .unique()
    )
    unique_technology = (
        dea_energy_storage_df["Technology"]
        .dropna()
        .astype(str)
        .str.casefold()
        .str.strip()
        .unique()
    )

    print(unique_year)
    print(unique_technology)

    print(dea_energy_storage_df.shape)
    filtered_df = dea_energy_storage_df.query(
        "not year.str.contains('uncertainty', case=False, na=False)", engine="python"
    )
    print(filtered_df.shape)

    # for year_val in unique_year:
    #    for tech_val in unique_technology:
    #        filtered_df = dea_energy_storage_df.query(
    #            "year.str.casefold() == year_val.casefold() and Technology.str.casefold()==tech_val.casefold()"
    #        )
