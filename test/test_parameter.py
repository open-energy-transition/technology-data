# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the initialization and methods of the Parameter class."""

import pathlib

import numpy as np
import pandas as pd
import pint
import pytest

from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.source_collection import SourceCollection
from technologydata.utils.units import extract_currency_units, ureg

path_cwd = pathlib.Path.cwd()


class TestParameter:
    """Test suite for the Parameter class in the technologydata module."""

    def test_parameter_creation(self) -> None:
        """Test the creation of a Parameter instance with various units."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
            carrier="H2",
            heating_value="LHV",
            provenance="literature",
            note="Estimated",
            sources=SourceCollection(
                sources=[
                    Source(
                        authors="some authors",
                        title="Example Title",
                    )
                ]
            ),
        )
        assert param.magnitude == 1000
        assert param.units == "USD_2020 / kilowatt"
        assert param.provenance == "literature"
        assert param.note == "Estimated"
        assert param.sources is not None

        # Internal pint quantities
        # pint autoconverts to the canonical name for the carrier and heating value
        # so comparing with == "H2" would fail; instead check that the units are compatible
        assert param._pint_quantity.units.is_compatible_with("USD_2020 / kW")
        assert param._pint_carrier.is_compatible_with("H2")
        assert param._pint_heating_value.is_compatible_with("LHV")

    def test_parameter_invalid_units(self) -> None:
        """Test that an error is raised when invalid units are provided."""
        with pytest.raises(pint.errors.UndefinedUnitError) as excinfo:
            Parameter(
                magnitude=1000,
                units="INVALID_UNIT",
            )
        assert "INVALID_UNIT" in str(excinfo.value)

        with pytest.raises(pint.errors.UndefinedUnitError) as excinfo:
            Parameter(
                magnitude=1000,
                units="USD_2020/kW",
                carrier="H2",
                heating_value="INVALID_HEATING_VALUE",
            )
        assert "INVALID_HEATING_VALUE" in str(excinfo.value)

        with pytest.raises(pint.errors.UndefinedUnitError) as excinfo:
            Parameter(
                magnitude=1000,
                units="USD_2020/kW",
                carrier="INVALID_CARRIER",
            )
        assert "INVALID_CARRIER" in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            Parameter(
                magnitude=1000,
                units="USD_2020/kW",
                heating_value="LHV",
            )
        assert "Heating value cannot be set without a carrier" in str(excinfo.value)

    def test_parameter_to_conversion_fail_on_currency_conversion(self) -> None:
        """Test the unit conversion of a Parameter instance to fail on currency conversion."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
        )
        with pytest.raises(NotImplementedError) as excinfo:
            param.to("EUR_2025 / kilowatt")
            assert "Currency conversion is not supported" in str(excinfo.value)

    def test_parameter_to_conversion(self) -> None:
        """Test the conversion of a Parameter instance to different units."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
        )

        ref = Parameter(
            magnitude=param.magnitude * 1000,
            units="USD_2020 / megawatt",
        )

        converted = param.to("USD_2020 / megawatt")

        assert isinstance(converted, Parameter)
        assert converted.units == ref.units
        assert converted.magnitude == ref.magnitude

    def test_pint_attributes_update(self) -> None:
        """Test that pint attributes are updated correctly when attributes change and a method that uses the pint fields is called."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
            carrier="H2",
            heating_value="LHV",
            provenance="literature",
            note="Estimated",
        )
        # Change magnitude and units
        param.magnitude = 2000
        param.units = "EUR_2025 / kilowatt"
        param._update_pint_attributes()
        assert param._pint_quantity.magnitude == 2000
        assert str(param._pint_quantity.units) == "EUR_2025 / kilowatt"

        # Change magnitude and units again and check if they are updated
        # when calling a method that uses them
        param.magnitude = 3000
        param.units = "USD_2020 / kWh"
        param = param.to("USD_2020 / kWh")
        assert param._pint_quantity.magnitude == 3000
        assert str(param._pint_quantity.units) == str(ureg.Unit("USD_2020 / kWh"))

    def test_parameter_change_currency(self) -> None:
        """Test currency conversion with inflation adjustment."""
        param = Parameter(
            magnitude=1,
            units="USD_2020/kW",
        )

        # Convert to EUR with inflation adjustment for Germany
        converted = param.change_currency("EUR_2023", "DEU")
        assert isinstance(converted, Parameter)
        assert converted.units is not None
        assert "EUR_2023" in converted.units
        assert converted._pint_quantity is not None
        assert converted._pint_quantity.is_compatible_with("EUR_2023 / kW")

        # Check that magnitude changed due to currency conversion
        assert not np.isnan(converted.magnitude)
        assert converted.magnitude != param.magnitude

    def test_parameter_change_currency_explicit_source(self) -> None:
        """Test currency conversion with explicit inflation data source."""
        param = Parameter(
            magnitude=1,
            units="EUR_2019/MWh",
        )

        # Convert using IMF data source
        converted = param.change_currency("USD_2022", "USA", source="worldbank")
        assert isinstance(converted, Parameter)
        assert converted.units is not None
        assert "USD_2022" in converted.units
        assert converted._pint_quantity is not None
        assert not np.isnan(converted.magnitude)
        assert converted._pint_quantity.is_compatible_with("USD_2022 / MWh")

    def test_parameter_change_currency_different_source(self) -> None:
        """Test currency conversion with different inflation data source."""
        param = Parameter(
            magnitude=1,
            units="EUR_2019/MWh",
        )

        # Convert using IMF data source
        converted = param.change_currency("USD_2022", "USA", source="imf")
        assert isinstance(converted, Parameter)
        assert converted.units is not None
        assert "USD_2022" in converted.units
        assert converted._pint_quantity.is_compatible_with("USD_2022 / MWh")

    def test_parameter_change_currency_multiple_currencies(self) -> None:
        """Test currency conversion when units contain multiple currencies."""
        param = Parameter(
            magnitude=1,
            units="USD_2020 * EUR_2021 / kW",
        )

        # Convert all currencies to CNY_2023
        converted = param.change_currency("CNY_2023", "CHN")
        assert isinstance(converted, Parameter)
        # Both USD_2020 and EUR_2021 should be replaced with CNY_2023
        assert converted.units is not None
        assert "CNY_2023" in converted.units
        assert "USD_2020" not in converted.units
        assert "EUR_2021" not in converted.units

    def test_parameter_change_currency_same_currency(self) -> None:
        """Test currency conversion to the same currency (inflation adjustment only)."""
        param = Parameter(
            magnitude=1,
            units="USD_2019/kW",
        )

        # Convert to USD but different year (inflation adjustment)
        converted = param.change_currency("USD_2023", "USA")
        assert isinstance(converted, Parameter)
        assert converted.units == "USD_2023 / kilowatt"
        # Magnitude should change due to inflation adjustment
        assert not np.isnan(converted.magnitude)
        assert converted.magnitude != param.magnitude

    def test_parameter_no_currency_change(self) -> None:
        """Test that no currency change occurs when the target currency is the same as the current one."""
        param = Parameter(
            magnitude=1,
            units="USD_2020/kW",
        )

        # Convert to the same currency and year
        converted = param.change_currency("USD_2020", "USA")
        assert isinstance(converted, Parameter)
        assert converted._pint_quantity.is_compatible_with("USD_2020 / kW")
        # Magnitude should remain unchanged
        assert not np.isnan(converted.magnitude)
        assert converted.magnitude == param.magnitude

    def test_parameter_change_currency_invalid_country(self) -> None:
        """Test that invalid country codes raise appropriate errors."""
        param = Parameter(
            magnitude=1,
            units="USD_2020/kW",
        )

        # Invalid country code should raise an error
        with pytest.raises((ValueError, KeyError)):
            param.change_currency("EUR_2023", "USB")

    def test_parameter_change_currency_invalid_source(self) -> None:
        """Test that invalid inflation data sources raise appropriate errors."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
        )

        # Invalid source should raise an error
        with pytest.raises(KeyError):
            param.change_currency("EUR_2023", "DEU", source="invalid_source")

    def test_parameter_change_currency_no_units(self) -> None:
        """Test currency conversion with parameter that has no units."""
        param = Parameter(
            magnitude=42,
        )

        # Should handle parameters without currency units gracefully
        converted = param.change_currency("EUR_2023", "DEU")
        assert isinstance(converted, Parameter)
        assert converted.magnitude == 42
        assert converted.units is None or "EUR_2023" not in str(converted.units)

    def test_parameter_unchanged_other_attributes(self) -> None:
        """Test that other attributes remain unchanged after currency conversion."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
            carrier="H2",
            heating_value="LHV",
            provenance="literature",
            note="Estimated",
        )

        # Convert to EUR_2023
        converted = param.change_currency("EUR_2023", "DEU")

        # Check that other attributes remain unchanged
        assert converted.carrier == param.carrier
        assert converted.heating_value == param.heating_value
        assert converted.provenance == param.provenance
        assert converted.note == param.note

    def test_parameter_heating_value_compatibility(self) -> None:
        """Test that we do not permit operations on mixed heating values."""
        param_lhv = Parameter(
            magnitude=1,
            carrier="H2",
            heating_value="LHV",
        )
        param_hhv = Parameter(
            magnitude=1,
            carrier="H2",
            heating_value="HHV",
        )

        # Different error messages for + and -
        with pytest.raises(ValueError) as excinfo:
            param_lhv + param_hhv
            assert (
                "Operation not permitted on parameters with different heating values"
                in str(excinfo.value)
            )
        with pytest.raises(ValueError) as excinfo:
            param_lhv - param_hhv
            assert (
                "Operation not permitted on parameters with different heating values"
                in str(excinfo.value)
            )

        # Different error messages for * and /
        with pytest.raises(ValueError) as excinfo:
            param_lhv * param_hhv
            assert "Cannot multiply parameters with different heating values" in str(
                excinfo.value
            )

        with pytest.raises(ValueError) as excinfo:
            param_lhv / param_hhv
            assert "Cannot divide parameters with different heating values" in str(
                excinfo.value
            )

    def test_parameter_carrier_compatibility(self) -> None:
        """Test that we do only permit certain operations on mixed carriers."""
        param_h2 = Parameter(
            magnitude=1,
            carrier="H2",
            heating_value="LHV",
        )
        param_ch4 = Parameter(
            magnitude=1,
            carrier="CH4",
            heating_value="LHV",
        )

        # Different error messages for + and -
        with pytest.raises(ValueError) as excinfo:
            param_h2 + param_ch4
            assert (
                "Operation not permitted on parameters with different carriers"
                in str(excinfo.value)
            )
        with pytest.raises(ValueError) as excinfo:
            param_h2 - param_ch4
            assert (
                "Operation not permitted on parameters with different carriers"
                in str(excinfo.value)
            )

        # * and / are permitted with different carriers and should yield mixed carriers
        assert (
            param_h2 * param_ch4
        ).carrier == param_h2._pint_carrier * param_ch4._pint_carrier
        assert (
            param_h2 / param_ch4
        ).carrier == param_h2._pint_carrier / param_ch4._pint_carrier

    def test_parameter_equality(self) -> None:
        """Test equality comparison of Parameter objects."""
        # Create two identical parameters
        param1 = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
            carrier="H2",
            heating_value="LHV",
            provenance="literature",
            note="Estimated",
            sources=SourceCollection(
                sources=[
                    Source(
                        authors="some authors",
                        title="Example Title",
                    )
                ]
            ),
        )
        param2 = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
            carrier="H2",
            heating_value="LHV",
            provenance="literature",
            note="Estimated",
            sources=SourceCollection(
                sources=[
                    Source(
                        authors="some authors",
                        title="Example Title",
                    )
                ]
            ),
        )

        # Should be equal
        assert param1 == param2
        assert param2 == param1

    def test_parameter_equality_different_magnitude(self) -> None:
        """Test that parameters with different magnitudes are not equal."""
        param1 = Parameter(magnitude=1000, units="USD_2020/kW")
        param2 = Parameter(magnitude=2000, units="USD_2020/kW")

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_different_units(self) -> None:
        """Test that parameters with different units are not equal."""
        param1 = Parameter(magnitude=1000, units="USD_2020/kW")
        param2 = Parameter(magnitude=1000, units="EUR_2020/kW")

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_different_carrier(self) -> None:
        """Test that parameters with different carriers are not equal."""
        param1 = Parameter(magnitude=1000, carrier="H2")
        param2 = Parameter(magnitude=1000, carrier="CH4")

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_different_heating_value(self) -> None:
        """Test that parameters with different heating values are not equal."""
        param1 = Parameter(magnitude=1000, carrier="H2", heating_value="LHV")
        param2 = Parameter(magnitude=1000, carrier="H2", heating_value="HHV")

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_different_provenance(self) -> None:
        """Test that parameters with different provenance are not equal."""
        param1 = Parameter(magnitude=1000, provenance="literature")
        param2 = Parameter(magnitude=1000, provenance="expert_estimate")

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_different_note(self) -> None:
        """Test that parameters with different notes are not equal."""
        param1 = Parameter(magnitude=1000, note="Estimated")
        param2 = Parameter(magnitude=1000, note="Measured")

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_different_sources(self) -> None:
        """Test that parameters with different sources are not equal."""
        source1 = Source(authors="Author A", title="Title A")
        source2 = Source(authors="Author B", title="Title B")

        param1 = Parameter(magnitude=1000, sources=SourceCollection(sources=[source1]))
        param2 = Parameter(magnitude=1000, sources=SourceCollection(sources=[source2]))

        assert param1 != param2
        assert param2 != param1

    def test_parameter_equality_none_values(self) -> None:
        """Test equality with None values for optional fields."""
        param1 = Parameter(magnitude=1000)
        param2 = Parameter(magnitude=1000)

        # Both have None for optional fields, should be equal
        assert param1 == param2

        # One has None, the other has a value
        param3 = Parameter(magnitude=1000, units="USD_2020/kW")
        assert param1 != param3
        assert param3 != param1

    def test_parameter_equality_with_non_parameter(self) -> None:
        """Test equality comparison with non-Parameter objects."""
        param = Parameter(magnitude=1000)

        # Should return NotImplemented for non-Parameter objects
        assert param.__eq__("not a parameter") == NotImplemented
        assert param.__eq__(42) == NotImplemented
        assert param.__eq__(None) == NotImplemented

    def test_parameter_equality_canonical_units(self) -> None:
        """Test that parameters with equivalent but differently formatted units are equal."""
        # Units should be canonicalized during initialization
        param1 = Parameter(magnitude=1000, units="USD_2020/kW")
        param2 = Parameter(magnitude=1000, units="USD_2020/kilowatt")

        # Should be equal because units are canonicalized
        assert param1 == param2
        assert param2 == param1

    def test_parameter_equality_self_reference(self) -> None:
        """Test that a parameter is equal to itself."""
        param = Parameter(
            magnitude=1000,
            units="USD_2020/kW",
            carrier="H2",
            heating_value="LHV",
            provenance="literature",
            note="Estimated",
        )

        assert param == param

    @pytest.mark.parametrize(
        "example_parameter",
        [
            {
                "parameter_magnitude": 1000,
                "parameter_units": "USD_2020/kW",
                "parameter_carrier": "H2",
                "parameter_heating_value": "LHV",
                "parameter_provenance": "literature",
                "parameter_note": "Estimated",
                "parameter_sources": [Source(title="title", authors="authors")],
            }
        ],
        indirect=["example_parameter"],
    )  # type: ignore
    def test_example_parameter(self, example_parameter: Parameter) -> None:
        """Test that the fixture example_parameter yields a parameter object."""
        assert isinstance(example_parameter, Parameter)

    def test_parameter_pow_basic(self) -> None:
        """Test integer exponentiation."""
        param = Parameter(magnitude=2, units="kW")
        result = param**3
        assert isinstance(result, Parameter)
        assert result.magnitude == 8
        assert result.units == "kilowatt ** 3"

    def test_parameter_pow_fractional(self) -> None:
        """Test fractional exponentiation."""
        param = Parameter(magnitude=9, units="m**2")
        result = param**0.5
        assert pytest.approx(result.magnitude) == 3
        assert result.units == "meter"

    def test_parameter_pow_zero(self) -> None:
        """Test zero exponent returns dimensionless."""
        param = Parameter(magnitude=5, units="J")
        result = param**0
        assert result.magnitude == 1
        assert result.units == "dimensionless"

    def test_parameter_pow_negative(self) -> None:
        """Test negative exponentiation and unit handling."""
        param = Parameter(magnitude=2, units="W")
        result = param**-2
        assert pytest.approx(result.magnitude) == 0.25
        # Compare units using pint, not string equality
        assert ureg.Unit(result.units) == ureg.Unit("watt ** -2")

    def test_parameter_pow_carrier(self) -> None:
        """Test that the carrier attribute is also affected."""
        param = Parameter(
            magnitude=3,
            units="kg",
            carrier="H2",
        )
        result = param**2
        assert result.carrier == f"{param.carrier} ** 2"

    def test_parameter_pow_preserves_metadata(self) -> None:
        """Test that metadata is preserved after exponentiation."""
        param = Parameter(
            magnitude=3,
            units="kg",
            carrier="H2",
            heating_value="LHV",
            provenance="test",
            note="note",
        )
        result = param**2
        assert result.carrier == f"{param.carrier} ** 2"
        assert result.heating_value == param.heating_value
        assert result.provenance == param.provenance
        assert result.note == param.note

    def test_change_heating_value_h2_lhv_to_hhv(self) -> None:
        """Test LHV to HHV conversion for H2."""
        p = Parameter(
            magnitude=119.6,
            units="kilowatt_hour",
            carrier="hydrogen",
            heating_value="lower_heating_value",
        )
        p2 = p.change_heating_value("higher_heating_value")
        assert pytest.approx(p2.magnitude) == 141.8
        assert p2.heating_value == "higher_heating_value"
        assert p2.carrier == "hydrogen"
        assert p2.units == "kilowatt_hour"

    def test_change_heating_value_h2_hhv_to_lhv(self) -> None:
        """Test HHV to LHV conversion for H2."""
        p = Parameter(
            magnitude=141.8,
            units="kilowatt_hour",
            carrier="hydrogen",
            heating_value="higher_heating_value",
        )
        p2 = p.change_heating_value("lower_heating_value")
        assert pytest.approx(p2.magnitude) == 119.6
        assert p2.heating_value == "lower_heating_value"
        assert p2.carrier == "hydrogen"
        assert p2.units == "kilowatt_hour"

    def test_change_heating_value_ch4_lhv_to_hhv(self) -> None:
        """Test LHV to HHV conversion for CH4."""
        p = Parameter(
            magnitude=10,
            units="kilowatt_hour",
            carrier="methane",
            heating_value="lower_heating_value",
        )
        p2 = p.change_heating_value("higher_heating_value")
        assert pytest.approx(p2.magnitude) == 11.1
        assert p2.heating_value == "higher_heating_value"
        assert p2.carrier == "methane"
        assert p2.units == "kilowatt_hour"

    def test_change_heating_value_ch4_hhv_to_lhv(self) -> None:
        """Test HHV to LHV conversion for CH4."""
        p = Parameter(
            magnitude=11.1,
            units="kilowatt_hour",
            carrier="methane",
            heating_value="higher_heating_value",
        )
        p2 = p.change_heating_value("lower_heating_value")
        assert pytest.approx(p2.magnitude) == 10.0
        assert p2.heating_value == "lower_heating_value"
        assert p2.carrier == "methane"
        assert p2.units == "kilowatt_hour"

    def test_change_heating_value_no_carrier_in_units(self) -> None:
        """Test conversion when carrier does not appear in units (should treat as 1 appearance)."""
        p = Parameter(
            magnitude=1,
            units="kilowatt_hour",
            carrier="hydrogen",
            heating_value="lower_heating_value",
        )
        p2 = p.change_heating_value("higher_heating_value")
        assert pytest.approx(p2.magnitude) == 1.418 / 1.196
        assert p2.heating_value == "higher_heating_value"
        assert p2.carrier == "hydrogen"
        assert p2.units == "kilowatt_hour"

    def test_change_heating_value_same_hv(self) -> None:
        """Test that no conversion occurs if heating value is unchanged."""
        p = Parameter(
            magnitude=1,
            units="kilowatt_hour",
            carrier="hydrogen",
            heating_value="lower_heating_value",
        )
        p2 = p.change_heating_value("lower_heating_value")
        assert p2.magnitude == 1
        assert p2.heating_value == "lower_heating_value"

    @pytest.mark.parametrize(
        "folder_id",
        ["WB_CNY_2020", "WB_EUR_2020", "WB_USD_2020"],
    )  # type: ignore
    def test_change_currency(self, folder_id: str) -> None:
        """Validate the currency conversion rates."""
        input_path = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "currency_conversion",
            folder_id,
            "parameters.csv",
        )
        input_df = pd.read_csv(input_path).reset_index()
        for _, row in input_df.iterrows():
            output_param = Parameter(
                magnitude=row["output_magnitude"],
                units=row["output_units"],
            )

            input_param = Parameter(
                magnitude=row["input_magnitude"],
                units=row["input_units"],
            )
            assert output_param == input_param.change_currency(
                to_currency=extract_currency_units(row["output_units"])[0],
                country=row["country"],
                source=row["source"],
            )
