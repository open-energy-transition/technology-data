# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Parser for version 0.13.4 of the raw/legacy_input_data/other.csv and raw/legacy_input_data/usa.csv datasets."""

import logging
import math
import pathlib
import re
from typing import Any

import pandas

from technologydata.parameter import Parameter
from technologydata.parsers.commons import (
    UnitCarrierHeatingValueExtractor,
    UnitPatternRegex,
)
from technologydata.parsers.data_parser_base import ParserBase
from technologydata.source import Source
from technologydata.source_collection import SourceCollection
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection
from technologydata.utils.commons import Commons

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


class LegacyInputDataV0134Parser(ParserBase):
    """Parser for v0.13.4 of the raw/legacy_input_data/other.csv and raw/legacy_input_data/usa.csv datasets."""

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
        - Standalone mass with carrier: t_{carrier}
        - Energy without carrier to mass with carrier: {energy}/t_{carrier}

        The function also normalizes malformed unit strings (e.g., tCO2 -> t_CO2) before
        pattern matching.

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
        ('USD_2023/(t/h)', '1/CO2', None)
        >>> _extract_units_carriers_heating_value("EUR/(tCO2/h)/km")
        ('EUR/(t/h)/km', '1/CO2', None)
        >>> _extract_units_carriers_heating_value("t_CH4")
        ('t', 'CH4', None)
        >>> _extract_units_carriers_heating_value("MWh/t_CO2")
        ('MWh/t', '1/CO2', 'LHV')

        """
        if not isinstance(input_unit, str):
            return input_unit, None, None

        # Normalize tCO2 to t_CO2 (handles cases like EUR/(tCO2/h)/km)
        input_unit = input_unit.replace("tCO2", "t_CO2")

        # Pattern 1: Currency with optional year and power/energy carrier
        match = re.match(UnitPatternRegex.CURRENCY_POWER_CARRIER.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_currency_power_carrier(
                match
            )

        # Pattern 2 & 3: Currency with mass carrier and time (with or without parentheses)
        match = re.match(UnitPatternRegex.CURRENCY_MASS_TIME.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_currency_mass_time(match)

        match = re.match(UnitPatternRegex.CURRENCY_MASS_TIME_PAREN.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_currency_mass_time(match)

        # Pattern 4: Energy ratio with carriers
        match = re.match(UnitPatternRegex.ENERGY_ENERGY_RATIO.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_energy_ratio(match)

        # Pattern 5: Mass/energy ratio with carriers (excludes el/th/thermal via regex)
        match = re.match(UnitPatternRegex.MASS_ENERGY_RATIO.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_mass_energy_ratio(match)

        # Pattern 6: Energy unit with el/th/thermal carrier to mass
        match = re.match(UnitPatternRegex.ENERGY_THERMAL_MASS.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_energy_thermal_mass(match)

        # Pattern 7: Currency with generic unit and carrier per time (in parentheses)
        match = re.match(UnitPatternRegex.CURRENCY_GENERIC_TIME_PAREN.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_currency_generic_time(match)

        # Pattern 8: Currency per mass/time with distance dimension
        match = re.match(UnitPatternRegex.CURRENCY_MASS_TIME_DISTANCE.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_currency_mass_time_distance(
                match
            )

        # Pattern 9: Currency with mass carrier (without time)
        match = re.match(UnitPatternRegex.CURRENCY_MASS_CARRIER.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_currency_mass_carrier(match)

        # Pattern 10: Power per distance per power with carriers
        match = re.match(UnitPatternRegex.POWER_DISTANCE_POWER.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_power_distance_power(match)

        # Pattern 11: Standalone mass with carrier
        match = re.match(UnitPatternRegex.MASS_CARRIER.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_mass_carrier(match)

        # Pattern 12: Energy without carrier to mass with carrier
        match = re.match(UnitPatternRegex.ENERGY_MASS_CARRIER.value, input_unit)
        if match:
            return UnitCarrierHeatingValueExtractor.process_energy_mass_carrier(match)

        # No pattern matched - return as-is
        return input_unit, None, None

    @staticmethod
    def _round_value(value: float, num_digits: int) -> float:
        """
        Round a value to num_digits decimals, keeping at least num_digits significant digits.

        Values below 1 would lose their significant digits when rounded to decimals
        (e.g. 1.9e-08 would become 0.0), so they are rounded to significant digits.

        Examples
        --------
        >>> LegacyInputDataV0134Parser._round_value(51259.5439606197, 3)
        51259.544
        >>> LegacyInputDataV0134Parser._round_value(1.94321e-08, 3)
        1.94e-08

        """
        if pandas.isna(value) or value == 0:
            return value
        decimals = max(num_digits, num_digits - 1 - math.floor(math.log10(abs(value))))
        return round(value, decimals)

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
            - 'region': Region identifier ('USA' or 'other')
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
        - The function groups the DataFrame by ["scenario", "year", "technology", "region"]
        - For each group, it creates a dictionary of Parameters
        - Each Technology is instantiated with group-specific attributes

        """
        list_techs = []

        if archive_source:
            source_usa = Source(
                title="Energy system technology data for the US",
                authors="Contributors to technology-data. Data source: manual_input_usa.csv",
                version="v0.13.4",
                url="https://github.com/PyPSA/technology-data/blob/master/inputs/US/manual_input_usa.csv",
            )
            source_usa.ensure_in_wayback()
            source_other = Source(
                title="Energy system technology data",
                authors="Contributors to technology-data. Data source: manual_input.csv",
                version="v0.13.4",
                url="https://github.com/PyPSA/technology-data/blob/master/inputs/manual_input.csv",
            )
            source_other.ensure_in_wayback()
            sources_combined = SourceCollection(sources=[source_usa, source_other])
            sources_combined.to_json(sources_path, output_schema=output_schema)
        else:
            sources_combined = SourceCollection.from_json(sources_path)

        # Create separate source collections for USA and other regions
        source_usa_collection = SourceCollection(sources=[sources_combined.sources[0]])
        source_other_collection = SourceCollection(
            sources=[sources_combined.sources[1]]
        )

        for (scenario, year, technology, region), group in dataframe.groupby(
            ["scenario", "year", "technology", "region"]
        ):
            parameters = {}
            financial_case_for_tech = None

            # Select appropriate source based on region
            sources_for_tech = (
                source_usa_collection if region == "USA" else source_other_collection
            )

            for _, row in group.iterrows():
                unit, carrier, heating_value = (
                    LegacyInputDataV0134Parser._extract_units_carriers_heating_value(
                        row["unit"]
                    )
                )
                param_kwargs = {
                    "magnitude": row["value"],
                    "sources": sources_for_tech,
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

            # Use region from dataframe, convert empty string to actual value or keep as is
            region_value = region if region else None

            list_techs.append(
                Technology(
                    name=technology,
                    region=region_value,
                    year=year,
                    parameters=parameters,
                    case=case_value,
                    detailed_technology=technology,
                )
            )

        return TechnologyCollection(technologies=list_techs)

    def parse(
        self,
        input_path: pathlib.Path | list[pathlib.Path],
        num_digits: int,
        archive_source: bool,
        **kwargs: Any,
    ) -> None:
        """
        Parse and process version 0.13.4 of the raw/legacy_input_data/usa.csv and raw/legacy_input_data/other.csv datasets.

        This method reads the raw data from both CSV files (usa.csv and other.csv), cleans and
        transforms it through a series of steps, and then builds a TechnologyCollection.
        The processed data is saved to JSON files.

        Data processing steps include:
        - USA data is tagged with region='USA', other data with region='other'
        - Unit normalization: tCO2 -> t_CO2, MWHh_el -> MWh_el, MWhth -> MWh_th,
          kWel -> kW_el, MWh_thdh -> MWh_th, t_cl -> t_clinker,
          t_HLOHC -> t_H18DBT, t_LOHC -> t_H0DBT, t_hbi -> t_HBI
        - Removal of design point suffix: ,dp removed from units
        - Distance normalization: 1000km -> m (with value divided by 1e6)
        - Percentage conversion: 'per unit' -> '%' (with value multiplied by 100)
        - Rounding of all values to num_digits decimals, keeping at least
          num_digits significant digits
        - Currency year integration: currency_year column merged into unit string
        - Unit/carrier/heating value extraction using regex pattern matching

        Parameters
        ----------
        input_path : pathlib.Path | list[pathlib.Path]
            List of paths to the raw input data files. Must contain two CSV files:
            one with 'usa' or 'us' in the filename, and one 'other' file.
        num_digits : int
            Number of decimals to round numerical values to; values below 1 keep
            at least num_digits significant digits.
        archive_source : bool
            If True, archives the source object on the Wayback Machine.
        **kwargs : bool
            export_schema : bool
                If True, exports the Pydantic schema for the data models.
            filter_params : bool
                Ignored by this parser.

        Raises
        ------
        TypeError
            If input_path is a single Path instead of a list.
        ValueError
            If the USA file or other file cannot be identified from the filenames.
        
        Returns
        -------
        Nothing

        Notes
        -----
        Writes parsed files to `src/technologydata/parsers/legacy_input_data/v0.13.4/`.

        """
        # Validate that input_path is a single Path, not a list
        if isinstance(input_path, pathlib.Path):
            raise TypeError(
                "LegacyInputDataV0134Parser requires a list of paths to the input files. "
            )

        export_schema = kwargs.get("export_schema", False)

        # Identify which file is USA and which is other based on filename
        usa_path = None
        other_path = None

        for file_path in input_path:
            if "usa" in file_path.name.casefold() or "us" in file_path.name.casefold():
                usa_path = file_path
            else:
                other_path = file_path

        # Validate we found both files
        if usa_path is None:
            raise ValueError(
                f"Could not find USA file (expected filename containing 'usa' or 'us'). "
                f"Got files: {[p.name for p in input_path]}"
            )
        if other_path is None:
            raise ValueError(
                f"Could not find 'other' file. Got files: {[p.name for p in input_path]}"
            )

        # Read USA data
        legacy_input_data_usa_df = pandas.read_csv(
            usa_path, dtype=str, na_values="None"
        )
        legacy_input_data_usa_df["value"] = legacy_input_data_usa_df["value"].astype(
            float
        )
        legacy_input_data_usa_df["scenario"] = legacy_input_data_usa_df[
            "scenario"
        ].fillna("not_available")
        # Add region column for USA data
        legacy_input_data_usa_df["region"] = "USA"
        logger.info("USA data loaded with region='USA'.")

        # Read other data
        legacy_input_data_other_df = pandas.read_csv(
            other_path, dtype=str, na_values="None"
        )
        legacy_input_data_other_df["value"] = legacy_input_data_other_df[
            "value"
        ].astype(float)

        # Perform change: MWHh_el -> MWh_el
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("MWHh_el", "MWh_el")

        # Perform change: MWhth -> MWh_th
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("MWhth", "MWh_th", regex=False)

        # Perform change: tCO2 -> t_CO2
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("tCO2", "t_CO2", regex=False)

        # Perform change: kW_th,dp -> kW_th
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace(",dp", "", regex=False)

        # Perform change: MWh_thdh -> MWh_th
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("MWh_thdh", "MWh_th", regex=False)

        # Perform change: t_cl -> t_clinker
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("t_cl/", "t_clinker/", regex=False)

        # Perform change: t_HLOHC -> t_H18DBT (loaded LOHC)
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("t_HLOHC", "t_H18DBT", regex=False)

        # Perform change: t_LOHC -> t_H0DBT (unloaded LOHC)
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("t_LOHC", "t_H0DBT", regex=False)

        # Perform change: t_hbi -> t_HBI
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("t_hbi", "t_HBI", regex=False)

        # Perform change: EUR/kWel -> EUR/kW_el
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("EUR/kWel", "EUR/kW_el")

        # Perform change: t_FTfuel -> t_FT
        legacy_input_data_other_df["unit"] = legacy_input_data_other_df[
            "unit"
        ].str.replace("t_FTfuel", "t_FT")

        # Add missing columns for other.csv
        legacy_input_data_other_df["scenario"] = "not_available"
        legacy_input_data_other_df["financial_case"] = None
        # Add region column for other data
        legacy_input_data_other_df["region"] = "other"
        logger.info("Other data loaded with region='other' and missing columns added.")

        # Combine both dataframes
        legacy_input_data_df = pandas.concat(
            [legacy_input_data_usa_df, legacy_input_data_other_df],
            ignore_index=True,
        )
        logger.info("USA and other data combined.")

        # Normalize "p.u." to "per unit"
        legacy_input_data_df["unit"] = legacy_input_data_df["unit"].str.replace(
            "p.u.", "per unit", regex=False
        )

        # Replace "1000km" with "m" (no SI prefix) and divide val by 1e6
        mask_1000km = legacy_input_data_df["unit"].str.contains(
            "1000km", na=False, regex=False
        )
        legacy_input_data_df.loc[mask_1000km, "unit"] = legacy_input_data_df.loc[
            mask_1000km, "unit"
        ].str.replace("1000km", "m", regex=False)
        legacy_input_data_df.loc[mask_1000km, "value"] = (
            legacy_input_data_df.loc[mask_1000km, "value"] / 1e6
        )
        logger.info("`1000km` replaced by `m`. Corresponding value divided by 1e6.")

        # Replace "per unit" with "%" and multiply val by 100
        mask_per_unit = legacy_input_data_df["unit"].str.contains("per unit", na=False)
        legacy_input_data_df.loc[mask_per_unit, "unit"] = legacy_input_data_df.loc[
            mask_per_unit, "unit"
        ].str.replace("per unit", "%")
        legacy_input_data_df.loc[mask_per_unit, "value"] = (
            legacy_input_data_df.loc[mask_per_unit, "value"] * 100.0
        )
        logger.info(
            "`per unit` replaced by `%`. Corresponding value multiplied by 100."
        )

        # Round all values after the unit conversions
        legacy_input_data_df["value"] = legacy_input_data_df["value"].apply(
            lambda value: LegacyInputDataV0134Parser._round_value(value, num_digits)
        )

        # Include currency_year in unit if applicable
        legacy_input_data_df["unit"] = legacy_input_data_df.apply(
            lambda row: Commons.update_unit_with_currency_year(
                row["unit"], row["currency_year"]
            ),
            axis=1,
        )
        logger.info("`currency_year` included in `unit` column.")

        # Build TechnologyCollection
        legacy_input_data_output_base_path = pathlib.Path(
            path_cwd,
            "src",
            "technologydata",
            "parsers",
            "legacy_input_data",
        )
        output_technologies_path = pathlib.Path(
            legacy_input_data_output_base_path,
            "v0.13.4/technologies.json",
        )
        output_sources_path = pathlib.Path(
            legacy_input_data_output_base_path,
            "v0.13.4/sources.json",
        )

        tech_col = LegacyInputDataV0134Parser._build_technology_collection(
            legacy_input_data_df,
            output_sources_path,
            archive_source=archive_source,
            output_schema=export_schema,
        )

        logger.info("TechnologyCollection object instantiated.")
        tech_col.to_json(output_technologies_path, output_schema=export_schema)
        logger.info("TechnologyCollection object exported to json.")
