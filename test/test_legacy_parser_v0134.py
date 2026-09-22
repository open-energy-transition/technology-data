# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Test the functions of the legacy data parser."""

import pytest

from technologydata.parsers.legacy_input_data import LegacyInputDataV0134Parser


class TestLegacyDataParserV0134:
    """Test suite for the functions of the legacy data parser."""

    @pytest.mark.parametrize(
        ("input_unit", "expected_unit", "expected_carrier", "expected_heating"),
        [
            ("USD_2022/MW_FT", "USD_2022/MW", "1/FT", "1/LHV"),
            ("MWh_H2/MWh_FT", "MWh/MWh", "H2/FT", "LHV"),
            ("MWh_el/MWh_FT", "MWh/MWh", "el/FT", "LHV"),
            ("t_CO2/MWh_FT", "t/MWh", "CO2/FT", "LHV"),
            ("USD_2022/kWh_H2", "USD_2022/kWh", "1/H2", "LHV"),
            ("MWh_el/MWh_H2", "MWh/MWh", "el/H2", "LHV"),
            ("USD_2023/t_CO2/h", "USD_2023/t/h", "1/CO2", None),
            ("MWh_el/t_CO2", "MWh/t", "el/CO2", "LHV"),
            ("MWh_th/t_CO2", "MWh/t", "thermal/CO2", "LHV"),
            ("EUR/MW_FT", "EUR/MW", "1/FT", "1/LHV"),
            ("EUR/MW_CH4", "EUR/MW", "1/CH4", "1/LHV"),
            ("EUR/MW_H2", "EUR/MW", "1/H2", "1/LHV"),
            ("EUR/MW_MeOH", "EUR/MW", "1/MeOH", "1/LHV"),
            ("EUR/kW_CH4", "EUR/kW", "1/CH4", "1/LHV"),
            ("EUR/kW_H2", "EUR/kW", "1/H2", "1/LHV"),
            ("EUR/kWh_H2", "EUR/kWh", "1/H2", "LHV"),
            ("EUR/MWh_H2", "EUR/MWh", "1/H2", "LHV"),
            ("EUR/MWh_NH3", "EUR/MWh", "1/NH3", "LHV"),
            ("EUR/MWh_kerosene", "EUR/MWh", "1/kerosene", "LHV"),
            ("MWh_H2/MWh_CH4", "MWh/MWh", "H2/CH4", "LHV"),
            ("MWh_H2/MWh_MeOH", "MWh/MWh", "H2/MeOH", "LHV"),
            ("MWh_H2/MWh_NH3", "MWh/MWh", "H2/NH3", "LHV"),
            ("MWh_H2/MWh_kerosene", "MWh/MWh", "H2/kerosene", "LHV"),
            ("MWh_NH3/MWh_H2", "MWh/MWh", "NH3/H2", "LHV"),
            ("MWh_el/MWh_CH4", "MWh/MWh", "el/CH4", "LHV"),
            ("MWh_el/MWh_MeOH", "MWh/MWh", "el/MeOH", "LHV"),
            ("MWh_el/MWh_NH3", "MWh/MWh", "el/NH3", "LHV"),
            ("MWh_th/MWh_MeOH", "MWh/MWh", "thermal/MeOH", "LHV"),
            ("t_CO2/MWh_CH4", "t/MWh", "CO2/CH4", "LHV"),
            ("t_CO2/MWh_MeOH", "t/MWh", "CO2/MeOH", "LHV"),
            ("EUR/t_CO2/h", "EUR/t/h", "1/CO2", None),
            ("EUR/(tCO2/h)/km", "EUR/t/h/km", "1/CO2", None),
            ("MWh_H2/t_HLOHC", "MWh/t", "H2/HLOHC", "LHV"),
            ("MWh_el/t_HLOHC", "MWh/t", "el/HLOHC", "LHV"),
            ("t_LOHC/t_HLOHC", "t/t", "LOHC/HLOHC", None),
            ("EUR/(t_HVC/h)", "EUR/t/h", "1/HVC", None),
            ("MWh_el/t_HVC", "MWh/t", "el/HVC", "LHV"),
            ("MWh_MeOH/t_HVC", "MWh/t", "MeOH/HVC", "LHV"),
            ("t_CO2/t_HVC", "t/t", "CO2/HVC", None),
            ("MWh_naphtha/t_HVC", "MWh/t", "naphtha/HVC", "LHV"),
            ("EUR/t_cement/h", "EUR/t/h", "1/cement", None),
            ("MWh_el/t_cement", "MWh/t", "el/cement", "LHV"),
            ("MWh_el/t_clinker", "MWh/t", "el/clinker", "LHV"),
            ("EUR/t_steel/h", "EUR/t/h", "1/steel", None),
            ("MWh_el/t_steel", "MWh/t", "el/steel", "LHV"),
            ("MWh_NG/MWh_H2", "MWh/MWh", "NG/H2", "LHV"),
            ("MWh_coal/MWh_H2", "MWh/MWh", "coal/H2", "LHV"),
            ("MWh_oil/MWh_H2", "MWh/MWh", "oil/H2", "LHV"),
            ("MWh_wood/MWh_H2", "MWh/MWh", "wood/H2", "LHV"),
        ],
    )  # type: ignore
    def test_extract_units_carriers_heating_value(
        self,
        input_unit: str,
        expected_unit: str,
        expected_carrier: str | None,
        expected_heating: str | None,
    ) -> None:
        """Test extraction of units, carriers, and heating values."""
        result = LegacyInputDataV0134Parser._extract_units_carriers_heating_value(
            input_unit
        )
        assert result == (expected_unit, expected_carrier, expected_heating)
