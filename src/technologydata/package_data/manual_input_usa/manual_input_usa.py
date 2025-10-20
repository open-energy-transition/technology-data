# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Data parser for the manual_input_usa.csv data set."""

import argparse
import logging
import pathlib

import pandas

from technologydata import (
    Parameter,
    Source,
    SourceCollection,
    Technology,
    TechnologyCollection,
)

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


def update_unit_with_currency_year(series: pandas.Series) -> pandas.Series:
    """
    Update unit string to include currency year for USD-based units.

    Parameters
    ----------
    series : pandas.Series
        A series containing two elements: [unit, currency_year]

    Returns
    -------
    pandas.Series
        Updated series with modified unit

    Examples
    --------
    >>> update_unit_with_currency_year(["USD/Kwh", "2020"])
    USD_2020/KwH

    """
    unit, currency_year = series

    # Check if unit is a string, contains 'EUR', and price_year is not null
    if isinstance(unit, str) and "USD" in unit and pandas.notna(currency_year):
        # Replace 'EUR/' with 'EUR_{price_year}/'
        unit = unit.replace("USD", f"USD_{int(currency_year)}")

    return pandas.Series([unit, currency_year])


def standardize_units(unit: str) -> str:
    """
    Standardized units.

    Parameters
    ----------
    unit : str
        A string containing the unit to standardize

    Returns
    -------
    str
        Updated unit string.

    """
    # Mapping of incorrect units to correct units
    unit_corrections = {
        "MW_FT": "MW",
        "MWh_FT": "MWh",
        "MWh_H2": "MWh",
        "MWh_el": "MWh",
        "t_CO2": "tonne",
        "kWh_H2": "kWh",
        "MWh_th": "MWh",
    }

    # Replace wrong units
    for incorrect, correct in unit_corrections.items():
        if incorrect == unit or incorrect in unit:
            unit = unit.replace(incorrect, correct)

    return unit


def build_technology_collection(
    dataframe: pandas.DataFrame,
    sources_path: pathlib.Path,
    store_source: bool = False,
) -> TechnologyCollection:
    """
    Compute a collection of technologies from a grouped DataFrame.

    Processes input DataFrame by grouping technologies and extracting their parameters,
    creating Technology instances for each unique group.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Input DataFrame containing technology parameters.
        Expected columns include:
        - 'scenario': Estimation or case identifier
        - 'year': Year of the technology
        - 'technology': Detailed technology name
        - 'parameter': Parameter name
        - 'value': Parameter value
        - 'unit': Parameter units
        - 'further_description': Extra information about the technology
        - 'financial_case': Technology financial case
    sources_path: pathlib.Path
        Output path for storing the SourceCollection object
    store_source: Optional[bool]
        Flag to decide whether to store the source object on the Wayback Machine. Default False.

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

    if store_source:
        source = Source(
            title="Energy system technology data for the US",
            authors="Contributors to technology-data. Data source: manual_input_usa.csv",
            url="https://github.com/PyPSA/technology-data/blob/master/inputs/US/manual_input_usa.csv",
        )
        source.ensure_in_wayback()
        sources = SourceCollection(sources=[source])
        sources.to_json(sources_path)
    else:
        sources = SourceCollection.from_json(sources_path)

    for (scenario, year, technology), group in dataframe.groupby(
        ["scenario", "year", "technology"]
    ):
        for _, row in group.iterrows():
            parameters[row["parameter"]] = Parameter(
                magnitude=row["value"],
                units=row["unit"],
                note=row["further_description"],
                provenance=row["financial_case"],
                sources=sources,
            )
        list_techs.append(
            Technology(
                name=technology,
                region="US",
                year=year,
                parameters=parameters,
                case=scenario,
                detailed_technology=technology,
            )
        )
    return TechnologyCollection(technologies=list_techs)


def parse_input_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command line arguments containing:
        - Number of significant digits
        - Store source flag

    """
    # Create the parser
    parser = argparse.ArgumentParser(
        description="Parse the DEA technology storage dataset",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Define arguments
    parser.add_argument(
        "--num_digits",
        type=int,
        default=4,
        help="Name of significant digits to round the values. ",
    )

    parser.add_argument(
        "--store_source",
        action="store_true",
        help="Store_source, store the source object on the wayback machine. Default: false",
    )

    # Parse arguments
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    # Parse input arguments
    input_args = parse_input_arguments()
    logger.info("Command line arguments parsed.")

    manual_input_usa_input_path = pathlib.Path(
        path_cwd,
        "src",
        "technologydata",
        "package_data",
        "raw",
        "manual_input_usa.csv",
    )

    manual_input_usa_df = pandas.read_csv(manual_input_usa_input_path, dtype=str)

    # Standardize units
    manual_input_usa_df["unit"] = manual_input_usa_df["unit"].apply(standardize_units)
    logger.info("Units standardized.")

    # Include currency_year in unit if applicable
    manual_input_usa_df[["unit", "currency_year"]] = manual_input_usa_df[
        ["unit", "currency_year"]
    ].apply(update_unit_with_currency_year, axis=1)
    logger.info("`currency_year` included in `unit` column.")

    print(manual_input_usa_df["unit"].unique())

    # Build TechnologyCollection
    manual_input_usa_base_path = pathlib.Path(
        path_cwd,
        "src",
        "technologydata",
        "package_data",
        "manual_input_usa",
    )
    output_technologies_path = pathlib.Path(
        manual_input_usa_base_path,
        "technologies.json",
    )
    output_sources_path = pathlib.Path(
        manual_input_usa_base_path,
        "sources.json",
    )

    tech_col = build_technology_collection(
        manual_input_usa_df, output_sources_path, store_source=input_args.store_source
    )

    logger.info("TechnologyCollection object instantiated.")
    tech_col.to_json(output_technologies_path)
    logger.info("TechnologyCollection object exported to json.")
