# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Parser for version 0.13.4 of the legacy_data/other.csv and legacy_data/usa.csv datasets."""

import logging
import pathlib
import re
from typing import Any

import pandas

from technologydata.parameter import Parameter
from technologydata.parsers.commons import UnitPatternRegex
from technologydata.parsers.data_parser_base import ParserBase
from technologydata.source import Source
from technologydata.source_collection import SourceCollection
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection
from technologydata.utils.commons import Commons

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


class LegacyDataV0134Parser(ParserBase):
    """Parser for v0.13.4 of the legacy_data/other.csv and legacy_data/usa.csv datasets."""

    @staticmethod
    def _extract_units_carriers_heating_value(
        input_unit: str,
    ) -> tuple[str, str | None, str | None]:
        """
        Extract standardized units and carriers from an input unit string using regex patterns.

        This function uses regex pattern matching to extract unit, carrier, and heating value
        from complex unit strings. It handles various patterns including:
        - Currency-based units: {CURRENCY}[_{YEAR}]/{unit}_{carrier}
        - Energy ratio units: {unit1}_{carrier1}/{unit2}_{carrier2}
        - Mass/energy ratios: t_{carrier1}/MWh_{carrier2}
        - Time-based units with /h suffix
        - Geographic distance-based units with /km

        Parameters
        ----------
        input_unit : str
            A specialized unit string to be converted.

        Returns
        -------
        tuple[str, str | None, str | None]
            A tuple containing three elements:
            - The first element is the standardized unit
            - The second element is the corresponding carrier (or None if not found)
            - The third element is the corresponding heating value (or None if not found)

        Examples
        --------
        >>> _extract_units_carriers_heating_value("USD_2022/MW_FT")
        ('USD_2022/MW', '1/FT', '1/LHV')
        >>> _extract_units_carriers_heating_value("EUR/kW_H2")
        ('EUR/kW', '1/H2', '1/LHV')
        >>> _extract_units_carriers_heating_value("MWh_H2/MWh_FT")
        ('MWh/MWh', 'H2/FT', 'LHV')
        >>> _extract_units_carriers_heating_value("USD_2023/t_CO2/h")
        ('USD_2023/t/h', '1/CO2', None)

        """
        if not isinstance(input_unit, str):
            return input_unit, None, None

        # Pattern 1: Currency with optional year and power/energy carrier
        match1 = re.match(UnitPatternRegex.CURRENCY_POWER_CARRIER.value, input_unit)
        if match1:
            currency, year, unit, carrier = match1.groups()
            standardized_unit = (
                f"{currency}_{year}/{unit}" if year else f"{currency}/{unit}"
            )
            carrier_str = f"1/{carrier}"
            # Distinguish between power (W) and energy (Wh) units
            heating_value = "LHV" if unit.endswith("h") else "1/LHV"
            return standardized_unit, carrier_str, heating_value

        # Pattern 2: Currency with optional year, mass carrier and time (without parentheses)
        match2 = re.match(UnitPatternRegex.CURRENCY_MASS_TIME.value, input_unit)
        if match2:
            currency, year, carrier = match2.groups()
            standardized_unit = f"{currency}_{year}/t/h" if year else f"{currency}/t/h"
            carrier_str = f"1/{carrier}"
            return standardized_unit, carrier_str, None

        # Pattern 3: Currency with optional year and mass/time in parentheses
        match3 = re.match(UnitPatternRegex.CURRENCY_MASS_TIME_PAREN.value, input_unit)
        if match3:
            currency, year, carrier = match3.groups()
            standardized_unit = f"{currency}_{year}/t/h" if year else f"{currency}/t/h"
            carrier_str = f"1/{carrier}"
            return standardized_unit, carrier_str, None

        # Pattern 4: Energy ratio with carriers
        match4 = re.match(UnitPatternRegex.ENERGY_ENERGY_RATIO.value, input_unit)
        if match4:
            unit1, carrier1, unit2, carrier2 = match4.groups()
            standardized_unit = f"{unit1}/{unit2}"
            # Normalize "th" to "thermal"
            normalized_carrier1 = "thermal" if carrier1 == "th" else carrier1
            normalized_carrier2 = "thermal" if carrier2 == "th" else carrier2
            carrier_str = f"{normalized_carrier1}/{normalized_carrier2}"
            heating_value = "LHV"
            return standardized_unit, carrier_str, heating_value

        # Pattern 5: Mass/energy ratio with carriers (excludes el/th/thermal via regex)
        match5 = re.match(UnitPatternRegex.MASS_ENERGY_RATIO.value, input_unit)
        if match5:
            unit1, carrier1, unit2, carrier2 = match5.groups()
            standardized_unit = f"{unit1}/{unit2}"
            carrier_str = f"{carrier1}/{carrier2}"
            # Determine heating value based on unit types
            heating_value_result = "LHV" if ("Wh" in unit1 or "Wh" in unit2) else None
            return standardized_unit, carrier_str, heating_value_result

        # Pattern 6: Energy unit with el/th/thermal carrier to mass
        match6 = re.match(UnitPatternRegex.ENERGY_THERMAL_MASS.value, input_unit)
        if match6:
            unit, carrier1, carrier2 = match6.groups()
            standardized_unit = f"{unit}/t"
            # Normalize "th" to "thermal"
            normalized_carrier1 = "thermal" if carrier1 == "th" else carrier1
            carrier_str = f"{normalized_carrier1}/{carrier2}"
            heating_value = "LHV"
            return standardized_unit, carrier_str, heating_value

        # Pattern 7: Currency with generic unit and carrier per time (in parentheses)
        match7 = re.match(
            UnitPatternRegex.CURRENCY_GENERIC_TIME_PAREN.value, input_unit
        )
        if match7:
            currency, year, unit_type, carrier = match7.groups()
            standardized_unit = (
                f"{currency}_{year}/{unit_type}/h"
                if year
                else f"{currency}/{unit_type}/h"
            )
            carrier_str = f"1/{carrier}"
            return standardized_unit, carrier_str, None

        # Pattern 8: Currency per mass/time with distance dimension
        match8 = re.match(
            UnitPatternRegex.CURRENCY_MASS_TIME_DISTANCE.value, input_unit
        )
        if match8:
            currency, year, carrier = match8.groups()
            standardized_unit = (
                f"{currency}_{year}/t/h/km" if year else f"{currency}/t/h/km"
            )
            carrier_str = f"1/{carrier}"
            return standardized_unit, carrier_str, None

        # No pattern matched - return as-is
        return input_unit, None, None

    @staticmethod
    def _build_technology_collection(
        dataframe: pandas.DataFrame,
        sources_path: pathlib.Path,
        archive_source: bool = False,
        output_schema: bool = False,
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
        archive_source: Optional[bool]
            Flag to decide whether to archive the source object on the Wayback Machine. Default False.
        output_schema : Optional[bool]
            Flag to decide whether to export the source collection schema. Default False.

        Returns
        -------
        TechnologyCollection
            A collection of Technology instances, each representing a unique
            technology group with its associated parameters.

        Notes
        -----
        - The function groups the DataFrame by ["scenario", "year", "technology"]
        - For each group, it creates a dictionary of Parameters
        - Each Technology is instantiated with group-specific attributes

        """
        list_techs = []

        if archive_source:
            source = Source(
                title="Energy system technology data for the US",
                authors="Contributors to technology-data. Data source: manual_input_usa.csv",
                url="https://github.com/PyPSA/technology-data/blob/master/inputs/US/manual_input_usa.csv",
            )
            source.ensure_in_wayback()
            sources = SourceCollection(sources=[source])
            sources.to_json(sources_path, output_schema=output_schema)
        else:
            sources = SourceCollection.from_json(sources_path)

        for (scenario, year, technology), group in dataframe.groupby(
            ["scenario", "year", "technology"]
        ):
            parameters = {}
            financial_case_for_tech = None
            for _, row in group.iterrows():
                unit, carrier, heating_value = (
                    LegacyDataV0134Parser._extract_units_carriers_heating_value(
                        row["unit"]
                    )
                )
                param_kwargs = {
                    "magnitude": row["value"],
                    "sources": sources,
                }
                if carrier is not None:
                    param_kwargs["carrier"] = carrier
                if heating_value is not None:
                    param_kwargs["heating_value"] = heating_value
                if unit is not None:
                    param_kwargs["units"] = unit
                if row["further_description"] is not None and isinstance(
                    row["further_description"], str
                ):
                    param_kwargs["note"] = row["further_description"]
                if row["financial_case"] is not None and isinstance(
                    row["financial_case"], str
                ):
                    financial_case_for_tech = str(row["financial_case"])
                parameters[row["parameter"]] = Parameter(**param_kwargs)

            # Combine scenario and financial_case for the case attribute
            case_value = str(scenario)
            if financial_case_for_tech is not None:
                case_value = f"{scenario} - {financial_case_for_tech}"

            list_techs.append(
                Technology(
                    name=technology,
                    region="USA",
                    year=year,
                    parameters=parameters,
                    case=case_value,
                    detailed_technology=technology,
                )
            )

        return TechnologyCollection(technologies=list_techs)

    def parse(
        self,
        input_path: pathlib.Path,
        num_digits: int,
        archive_source: bool,
        **kwargs: Any,
    ) -> None:
        """
        Parse and process version 0.13.4 of the legacy_data/usa.csv dataset.

        This method reads the raw data from an Excel file, cleans and transforms
        it through a series of steps, and then builds a TechnologyCollection.
        The processed data is saved to JSON files.

        Parameters
        ----------
        input_path : pathlib.Path
            Path to the raw input data file (Excel).
        num_digits : int
            Number of significant digits to round numerical values.
        archive_source : bool
            If True, archives the source object on the Wayback Machine.
        **kwargs : bool
            export_schema : bool
                If True, exports the Pydantic schema for the data models.

        Returns
        -------
        TechnologyCollection
            A collection of parsed technology data.

        """
        export_schema = kwargs.get("export_schema", False)

        legacy_data_usa_input_path = pathlib.Path(input_path)

        legacy_data_usa_df = pandas.read_csv(
            legacy_data_usa_input_path, dtype=str, na_values="None"
        )
        legacy_data_usa_df["value"] = legacy_data_usa_df["value"].astype(float)
        legacy_data_usa_df["scenario"] = legacy_data_usa_df["scenario"].fillna(
            "not_available"
        )

        # Replace "per unit" with "%" and multiply val by 100
        mask_per_unit = legacy_data_usa_df["unit"].str.contains("per unit")
        legacy_data_usa_df.loc[mask_per_unit, "unit"] = legacy_data_usa_df.loc[
            mask_per_unit, "unit"
        ].str.replace("per unit", "%")
        legacy_data_usa_df.loc[mask_per_unit, "value"] = (
            legacy_data_usa_df.loc[mask_per_unit, "value"] * 100.0
        ).round(num_digits)
        logger.info(
            "`per unit` replaced by `%`. Corresponding value multiplied by 100."
        )

        # Include currency_year in unit if applicable
        legacy_data_usa_df["unit"] = legacy_data_usa_df.apply(
            lambda row: Commons.update_unit_with_currency_year(
                row["unit"], row["currency_year"]
            ),
            axis=1,
        )
        logger.info("`currency_year` included in `unit` column.")

        # Build TechnologyCollection
        legacy_data_usa_base_path = pathlib.Path(
            path_cwd,
            "src",
            "technologydata",
            "parsers",
            "legacy_data",
        )
        output_technologies_path = pathlib.Path(
            legacy_data_usa_base_path,
            "v0.13.4/technologies.json",
        )
        output_sources_path = pathlib.Path(
            legacy_data_usa_base_path,
            "v0.13.4/sources.json",
        )

        tech_col = LegacyDataV0134Parser._build_technology_collection(
            legacy_data_usa_df,
            output_sources_path,
            archive_source=archive_source,
            output_schema=export_schema,
        )

        logger.info("TechnologyCollection object instantiated.")
        tech_col.to_json(output_technologies_path, output_schema=export_schema)
        logger.info("TechnologyCollection object exported to json.")
