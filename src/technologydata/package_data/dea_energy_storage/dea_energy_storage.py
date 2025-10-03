# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Data parser for the DEA energy storage data set."""

import csv
import logging
import pathlib
import re
import typing

import pandas

from technologydata import Parameter, Technology, TechnologyCollection

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


def drop_invalid_rows(dataframe: pandas.DataFrame) -> pandas.DataFrame:
    """
    Clean and filter a DataFrame by removing rows with invalid or incomplete data.

    This function performs multiple validation checks to ensure data quality:
    - Removes rows with None or NaN values in critical columns
    - Removes rows with empty or whitespace-only strings
    - Filters rows based on specific data integrity criteria
    - Discards rows where 'val' column contains comparator symbols or non-numeric values

    Parameters
    ----------
    dataframe : pd.DataFrame
        The input DataFrame to be cleaned and validated.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with invalid rows removed, maintaining data integrity.

    Notes
    -----
    Validation criteria include:
    - Non-empty 'Technology', 'par', and 'val' columns
    - 'year' column containing a valid 4-digit year
    - 'val' column containing only numeric values (no comparator symbols)

    """
    # Create a copy to avoid modifying the original DataFrame
    df_cleaned = dataframe.copy()

    # Validate column existence
    required_columns = ["Technology", "par", "val", "year"]
    missing_columns = [col for col in required_columns if col not in df_cleaned.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Remove rows with None or NaN values in critical columns
    df_cleaned = df_cleaned.dropna(subset=required_columns)

    # Remove rows with empty or whitespace-only strings
    for column in ["Technology", "par", "val", "year"]:
        df_cleaned = df_cleaned[df_cleaned[column].astype(str).str.strip() != ""]

    # Filter rows with valid year (4 consecutive digits)
    df_cleaned = df_cleaned[
        df_cleaned["year"].astype(str).str.contains(r"\d{4}", regex=True)
    ]

    # Remove rows with comparator symbols or without digits in 'val' column
    df_cleaned = df_cleaned[
        (~df_cleaned["val"].astype(str).str.contains(r"[<>≤≥]", regex=True))
        & (df_cleaned["val"].astype(str).str.contains(r"\d", regex=True))
    ]

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

    # Remove content inside square brackets including the brackets themselves
    result = re.sub(r"\[.*?\]", "", text_string)

    # Remove content inside square bracket and parenthesis including the brackets/parenthesis themselves
    result = re.sub(r"\[.*?\)", "", result)

    # Remove extra spaces resulting from the removal and set all to lower case
    result = re.sub(r"\s+", " ", result).strip().casefold()

    return result


def clean_technology_string(tech_str: str) -> str:
    """
    Clean a technology string by removing numeric patterns and standardizing case.

    This function preprocesses technology-related strings by:
    - Removing three-digit numeric patterns (with optional letter)
    - Stripping leading and trailing whitespace
    - Converting to lowercase for case-insensitive comparison

    Parameters
    ----------
    tech_str : str
        Input technology string to be cleaned.

    Returns
    -------
    str
        Cleaned technology string with:
        - Numeric patterns (like '123' or '456a') removed
        - Whitespace stripped
        - Converted to lowercase

    Raises
    ------
    Exception
        If string conversion or processing fails, logs the error and returns the original input.

    """
    try:
        # Remove three-digit patterns or three digits followed by a letter
        return re.sub(r"\d{3}[a-zA-Z]?", "", tech_str).strip().casefold()
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
    match = re.match(r"([+-]?\d*\.?\d+)×10([+-]?\d+)", s)
    if match:
        base, exponent = match.groups()
        return round(float(base), 4) * (10 ** int(exponent))

    # Replace comma with dot for decimal numbers
    s = s.replace(",", ".")
    try:
        return round(float(s), 4)
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


def update_unit_with_price_year(series: pandas.Series) -> pandas.Series:
    """
    Update unit string to include price year for EUR-based units.

    Parameters
    ----------
    series : pandas.Series
        A series containing two elements: [unit, price_year]

    Returns
    -------
    pandas.Series
        Updated series with modified unit

    """
    unit, price_year = series

    # Check if unit is a string, contains 'EUR', and price_year is not null
    if isinstance(unit, str) and "EUR" in unit and pandas.notna(price_year):
        # Replace 'EUR/' with 'EUR_{price_year}/'
        unit = unit.replace("EUR", f"EUR_{int(price_year)}")

    return pandas.Series([unit, price_year])


def clean_est_string(est_str: str) -> str:
    """
    Casefold the 'est' string, trim whitespace and replace `ctrl` with `control`.

    Parameters
    ----------
    est_str : str
        The input 'est' string to be cleaned.

    Returns
    -------
    str
        The cleaned 'est' string.

    """
    if est_str == "ctrl":
        cleaned_str = "control"
    else:
        cleaned_str = est_str.casefold().strip()
    return cleaned_str


def complete_missing_units(series: pandas.Series) -> pandas.Series:
    """
    Complete missing units based on parameter names.

    Parameters
    ----------
    series : pandas.Series
        A series containing two elements: [par, unit]

    Returns
    -------
    pandas.Series
        Updated series with completed unit if it was missing.

    """
    par, unit = series

    # Define a mapping of parameters to their corresponding units
    param_unit_map = {
        "energy storage capacity for one unit": "MWh",
        "typical temperature difference in storage": "hot/cold,K",
        "fixed o&m": "pct.investement/year",
        "lifetime in total number of cycles": "cycles",
        "cycle life": "cycles",
    }

    # If unit is missing or empty, try to fill it based on the parameter name
    if (not isinstance(unit, str)) or (unit.strip() == ""):
        unit = param_unit_map.get(par, unit)

    return pandas.Series([par, unit])


def compute_parameters_dict(dataframe: pandas.DataFrame) -> TechnologyCollection:
    """
    Compute a collection of technologies from a grouped DataFrame.

    Processes input DataFrame by grouping technologies and extracting their parameters,
    creating Technology instances for each unique group.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Input DataFrame containing technology parameters.
        Expected columns include:
        - 'est': Estimation or case identifier
        - 'year': Year of the technology
        - 'ws': Workspace or technology identifier
        - 'Technology': Detailed technology name
        - 'par': Parameter name
        - 'val': Parameter value
        - 'unit': Parameter units

    Returns
    -------
    TechnologyCollection
        A collection of Technology instances, each representing a unique
        technology group with its associated parameters.

    Notes
    -----
    - The function groups the DataFrame by 'est', 'year', 'ws', and 'Technology'
    - For each group, it creates a dictionary of Parameters
    - Each Technology is instantiated with group-specific attributes

    """
    parameters = {}
    list_techs = []
    for (est, year, ws, technology_name), group in dataframe.groupby(
        ["est", "year", "ws", "Technology"]
    ):
        for _, row in group.iterrows():
            parameters[row["par"]] = Parameter(magnitude=row["val"], units=row["unit"])
        list_techs.append(
            Technology(
                name=ws,
                region="EU",
                year=year,
                parameters=parameters,
                case=est,
                detailed_technology=technology_name,
            )
        )
    return TechnologyCollection(technologies=list_techs)


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
        dea_energy_storage_file_path, sheet_name="alldata_flat", engine="calamine"
    )

    print(f"Shape before cleaning: {dea_energy_storage_df.shape}")

    # Drop unnecessary rows
    cleaned_df = drop_invalid_rows(dea_energy_storage_df)

    # Clean parameter (par) column
    cleaned_df["par"] = cleaned_df["par"].apply(clean_parameter_string)

    # Complete missing units based on parameter names
    cleaned_df[["par", "unit"]] = cleaned_df[["par", "unit"]].apply(
        complete_missing_units, axis=1
    )

    # Clean technology (Technology) column
    cleaned_df["Technology"] = cleaned_df["Technology"].apply(clean_technology_string)

    # Clean ws column
    cleaned_df["ws"] = cleaned_df["ws"].apply(clean_technology_string)

    # Clean year column
    cleaned_df["year"] = cleaned_df["year"].apply(extract_year)

    # Format value (val) column
    cleaned_df["val"] = cleaned_df["val"].apply(format_val_number)

    # Include priceyear in unit if applicable
    cleaned_df[["unit", "priceyear"]] = cleaned_df[["unit", "priceyear"]].apply(
        update_unit_with_price_year, axis=1
    )

    # Clean est column
    cleaned_df["est"] = cleaned_df["est"].apply(clean_est_string)

    # Drop unnecessary columns
    columns_to_drop = ["cat", "priceyear", "ref"]
    cleaned_df = cleaned_df.drop(columns=columns_to_drop, errors="ignore")

    # Build TechnologyCollection
    tech_col = compute_parameters_dict(cleaned_df)
    tech_col.to_json(pathlib.Path("technologies.json"), pathlib.Path("dea_storage"))

    print(f"Shape after cleaning: {cleaned_df.shape}")

    default_kwargs = {
        "sep": ",",
        "index": False,
        "encoding": "utf-8",
        "quoting": csv.QUOTE_ALL,
    }

    cleaned_df.info()
    cleaned_df.to_csv("file.csv", **default_kwargs)

    # ======
    # SCHEMA
    # ======

    # Technology object (just mandatory fields)
    # ws -> Technology.name (str)
    # - -> Technology.region (str) --> this is missing
    # year -> Technology.year (int)
    # est -> Technology.case (str)
    # Technology -> Technology.detailed_technology (str)

    # Parameter object (mandatory fields and some more)
    # par -> key in parameters : Dict[str, Parameter] (str)
    # unit -> Parameter.units (str)
    # priceyear -> (str) currency year in the unit of Parameter --> need to write a method that if unit column contains currency, I need to add priceyear
    # note -> Parameter.note (str) --> need to write a method that links letter to description
    # val -> Parameter.magnitude (int, float)

    # Source object
    # Source.title (str) --> need to extract it from dictionary I need to build
    # Source.authors (str) --> need to extract it from dictionary I need to build

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
