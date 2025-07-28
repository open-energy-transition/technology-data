# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

import pint
import pytest

from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.source_collection import SourceCollection
from technologydata.utils.units import ureg


def test_parameter_creation() -> None:
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
                    name="Example Source", authors="some authors", title="Example Title"
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


def test_parameter_invalid_units() -> None:
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


def test_parameter_to_conversion_fail_on_currency_conversion() -> None:
    """Test the unit conversion of a Parameter instance to fail on currency conversion."""
    param = Parameter(
        magnitude=1000,
        units="USD_2020/kW",
    )
    with pytest.raises(NotImplementedError) as excinfo:
        param.to("EUR_2025 / kilowatt")
        assert "Currency conversion is not supported" in str(excinfo.value)


def test_parameter_to_conversion() -> None:
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


def test_pint_attributes_update() -> None:
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


def test_parameter_change_currency() -> None:
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
    assert converted.magnitude != param.magnitude


def test_parameter_change_currency_explicit_source() -> None:
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
    assert converted._pint_quantity.is_compatible_with("USD_2022 / MWh")


def test_parameter_change_currency_different_source() -> None:
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


def test_parameter_change_currency_multiple_currencies() -> None:
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


def test_parameter_change_currency_same_currency() -> None:
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
    assert converted.magnitude != param.magnitude


def test_parameter_no_currency_change() -> None:
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
    assert converted.magnitude == param.magnitude


def test_parameter_change_currency_invalid_country() -> None:
    """Test that invalid country codes raise appropriate errors."""
    param = Parameter(
        magnitude=1,
        units="USD_2020/kW",
    )

    # Invalid country code should raise an error
    with pytest.raises((ValueError, KeyError)):
        param.change_currency("EUR_2023", "USB")


def test_parameter_change_currency_invalid_source() -> None:
    """Test that invalid inflation data sources raise appropriate errors."""
    param = Parameter(
        magnitude=1000,
        units="USD_2020/kW",
    )

    # Invalid source should raise an error
    with pytest.raises(KeyError):
        param.change_currency("EUR_2023", "DEU", source="invalid_source")


def test_parameter_change_currency_no_units() -> None:
    """Test currency conversion with parameter that has no units."""
    param = Parameter(
        magnitude=42,
    )

    # Should handle parameters without currency units gracefully
    converted = param.change_currency("EUR_2023", "DEU")
    assert isinstance(converted, Parameter)
    assert converted.magnitude == 42
    assert converted.units is None or "EUR_2023" not in str(converted.units)


def test_parameter_unchanged_other_attributes() -> None:
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


def test_parameter_incompatible_heating_values() -> None:
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
