# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Data parser for the DEA energy storage data set."""

import logging
import pathlib
import re
import typing

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
    - The 'Technology', 'par', or 'val' columns are None or empty strings (including strings with only whitespace).
    - The 'year' or 'val' columns do not contain any digits.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        The input DataFrame to be cleaned.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame with rows containing invalid data removed.

    """
    # Drop rows where 'Technology', 'par', or 'val' are None
    df_cleaned = dataframe.dropna(subset=["Technology", "par", "val"])

    # Remove rows where 'Technology' is empty or whitespace
    df_cleaned = df_cleaned[~df_cleaned["Technology"].astype(str).str.strip().eq("")]

    # Remove rows where 'par' is empty or whitespace
    df_cleaned = df_cleaned[~df_cleaned["par"].astype(str).str.strip().eq("")]

    # Remove rows where 'val' is empty or whitespace
    df_cleaned = df_cleaned[~df_cleaned["val"].astype(str).str.strip().eq("")]

    # Keep only rows where 'year' contains at least four consecutive digits
    df_cleaned = df_cleaned[df_cleaned["year"].astype(str).str.contains(r"\d{4}")]

    # Remove rows where 'val' does not contain any digit
    df_cleaned = df_cleaned[df_cleaned["val"].astype(str).str.contains(r"\d")]

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


def format_val_number(input_value: str) -> float | None | typing.Any:
    """
    Parse various number formats into a float value.

    Parameters
    ----------
    input_value : str
        The input number in different formats, such as:
        - Scientific notation with "x10^": e.g., "2.84x10^23"
        - Numbers with commas as decimal separators: e.g., "1,1"

    Returns
    -------
    float
        The parsed numerical value as a float.

    Raises
    ------
    ValueError
        If the input cannot be parsed into a float.

    """
    s = str(input_value).strip()

    # Handle scientific notation like "2.84x10^23"
    match = re.match(r"([+-]?\d*\.?\d+)x10([+-]?\d+)", s)
    if match:
        base, exponent = match.groups()
        return float(base) * (10 ** int(exponent))

    # Replace comma with dot for decimal numbers
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"Cannot parse number from input: {input_value}")


def extract_year(year_str: str | int) -> int | None:
    """
    Extract the first year (integer) from a given input.

    Parameters
    ----------
    year_str : str
        Input value containing a potential year.

    Returns
    -------
    int, None
        Extracted first year.

    Examples
    --------
    >>> extract_year('uncertainty (2050)')
    2050
    >>> extract_year('some text 2025 more text')
    2025

    """
    if isinstance(year_str, str):
        # Extract digits
        digits = re.findall(r"\d+", year_str)

        # Convert to integer
        return int(digits[0]) if digits else None
    else:
        return year_str


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

    print(f"Shape before cleaning: {dea_energy_storage_df.shape}")

    # Drop unnecessary rows
    cleaned_df = drop_invalid_rows(dea_energy_storage_df)

    # Clean parameter (par) column
    cleaned_df["par"] = cleaned_df["par"].apply(
        clean_parameter_string
    )

    # Clean technology (Technology) column
    cleaned_df["Technology"] = cleaned_df["Technology"].apply(
        clean_technology_string
    )

    # Clean year column
    cleaned_df["year"] = cleaned_df["year"].apply(extract_year)

    # Format value (val) column
    cleaned_df["val"] = cleaned_df["val"].apply(format_val_number)

    print(f"Shape after cleaning: {cleaned_df.shape}")
    cleaned_df.to_csv("file.csv")

    # # Get unique values of technology-year pair
    # unique_year = (
    #     dea_energy_storage_df["year"]
    #     .dropna()
    #     .astype(str)
    #     .str.casefold()
    #     .str.strip()
    #     .unique()
    # )
    # unique_technology = (
    #     dea_energy_storage_df["Technology"]
    #     .dropna()
    #     .astype(str)
    #     .str.casefold()
    #     .str.strip()
    #     .unique()
    # )
    #
    # print(unique_year)
    # print(unique_technology)
    #
    # print(dea_energy_storage_df.shape)
    # filtered_df = dea_energy_storage_df.query(
    #     "not year.str.contains('uncertainty', case=False, na=False)", engine="python"
    # )
    # print(filtered_df.shape)
    #
    # # for year_val in unique_year:
    # #    for tech_val in unique_technology:
    # #        filtered_df = dea_energy_storage_df.query(
    # #            "year.str.casefold() == year_val.casefold() and Technology.str.casefold()==tech_val.casefold()"
    # #        )
