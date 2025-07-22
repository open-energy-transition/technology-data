# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

import pint

from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.source_collection import SourceCollection


def test_parameter_creation():
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


def test_parameter_to_conversion():
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


def test_pint_attributes_update():
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
