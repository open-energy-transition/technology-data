# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

import pint
import pytest

from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.source_collection import SourceCollection


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
    assert param.units == "USD_2020/kW"
    assert str(param._pint_quantity.units) == "USD_2020 / kilowatt"
    assert str(param._pint_carrier) == "H2"
    assert str(param._pint_heating_value) == "LHV"
    assert param.provenance == "literature"
    assert param.note == "Estimated"
    assert param.sources is not None


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


def test_parameter_to_conversion() -> None:
    """Test the conversion of a Parameter instance to different units."""
    param = Parameter(
        magnitude=1000,
        units="USD_2020/kW",
        carrier="H2",
        heating_value="LHV",
        provenance="literature",
        note="Estimated",
        sources=None,
    )
    converted = param.to("EUR_2025 / kilowatt")
    assert isinstance(converted, Parameter)
    assert converted.units == "EUR_2025 / kilowatt"
    assert (
        converted.magnitude == param._pint_quantity.to("EUR_2025 / kilowatt").magnitude
    )


def test_pint_attributes_update() -> None:
    """Test that pint attributes are updated correctly when attributes change and a method that uses the pint fields is called."""
    param = Parameter(
        magnitude=1000,
        units="USD_2020/kW",
        carrier="H2",
        heating_value="LHV",
        provenance="literature",
        note="Estimated",
        sources=None,
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
    assert str(param._pint_quantity.units) == str(pint.Unit("USD_2020 / kWh"))
