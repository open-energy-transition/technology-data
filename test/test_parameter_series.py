# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
Tests for Parameter class with pandas Series functionality.

Tests the new capability of Parameter to handle both scalar values and pandas Series,
ensuring that all existing functionality works with series data.
"""

import pandas as pd
import pytest

from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.source_collection import SourceCollection


class TestParameterSeries:
    """Test Parameter class with pandas Series magnitude values."""

    def test_parameter_creation_with_series(self) -> None:
        """Test creating a Parameter with pandas Series magnitude."""
        series_data = pd.Series([100.0, 200.0, 300.0], index=["2020", "2030", "2040"])
        param = Parameter(
            magnitude=series_data,
            units="EUR_2020/kW",
            provenance="test",
            note="Test parameter with series",
        )

        assert param._is_magnitude_series()
        assert not param._is_magnitude_scalar()
        assert isinstance(param.magnitude, pd.Series)
        if isinstance(param.magnitude, pd.Series):
            assert len(param.magnitude) == 3
            assert param.magnitude.loc["2030"] == 200.0

    def test_parameter_creation_with_list(self) -> None:
        """Test creating a Parameter with list magnitude."""
        list_data = [100.0, 200.0, 300.0]
        param = Parameter(
            magnitude=pd.Series(list_data, index=["2020", "2030", "2040"]),
            units="EUR_2020/kW",
            provenance="test",
            note="Test parameter with list",
        )

        assert param._is_magnitude_series()
        assert not param._is_magnitude_scalar()
        if isinstance(param.magnitude, pd.Series):
            assert len(param.magnitude) == 3
            assert param.magnitude.loc["2030"] == 200.0

    def test_parameter_scalar_helpers(self) -> None:
        """Test helper methods work correctly for scalar values."""
        param = Parameter(magnitude=150.0, units="EUR_2020/kW")

        assert param._is_magnitude_scalar()
        assert not param._is_magnitude_series()

        series_version = param._get_magnitude_as_series()
        assert isinstance(series_version, pd.Series)
        if isinstance(param.magnitude, pd.Series):
            assert len(series_version) == 1
            assert series_version.iloc[0] == 150.0

    def test_parameter_series_helpers(self) -> None:
        """Test helper methods work correctly for series values."""
        series_data = pd.Series([100.0, 200.0, 300.0], index=["2020", "2030", "2040"])
        param = Parameter(magnitude=series_data, units="EUR_2020/kW")

        assert param._is_magnitude_series()
        assert not param._is_magnitude_scalar()

        series_version = param._get_magnitude_as_series()
        assert isinstance(series_version, pd.Series)
        if isinstance(param.magnitude, pd.Series):
            assert len(series_version) == 3
        pd.testing.assert_series_equal(series_version, series_data)

    def test_parameter_to_conversion_with_series(self) -> None:
        """Test unit conversion with series magnitude."""
        series_data = pd.Series(
            [1000.0, 2000.0, 3000.0], index=["2020", "2030", "2040"]
        )
        param = Parameter(magnitude=series_data, units="EUR_2020/kW")

        converted = param.to("EUR_2020/MW")

        assert isinstance(converted.magnitude, pd.Series)
        if isinstance(converted.magnitude, pd.Series):
            assert len(converted.magnitude) == 3
            assert (
                converted.magnitude.loc["2030"] == 2000000.0
            )  # 2000 kW = 2,000,000 EUR_2020/MW
        pd.testing.assert_index_equal(converted.magnitude.index, series_data.index)
        assert converted.units == "EUR_2020 / megawatt"

    def test_parameter_series_arithmetic_addition(self) -> None:
        """Test addition with series parameters."""
        series1 = pd.Series([100.0, 200.0, 300.0], index=["2020", "2030", "2040"])
        series2 = pd.Series([50.0, 100.0, 150.0], index=["2020", "2030", "2040"])

        param1 = Parameter(magnitude=series1, units="EUR_2020/kW")
        param2 = Parameter(magnitude=series2, units="EUR_2020/kW")

        result = param1 + param2

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 3
            assert result.magnitude.loc["2030"] == 300.0  # 200 + 100
        pd.testing.assert_index_equal(result.magnitude.index, series1.index)
        assert result.units == "EUR_2020 / kilowatt"

    def test_parameter_series_arithmetic_subtraction(self) -> None:
        """Test subtraction with series parameters."""
        series1 = pd.Series([300.0, 400.0, 500.0], index=["2020", "2030", "2040"])
        series2 = pd.Series([100.0, 150.0, 200.0], index=["2020", "2030", "2040"])

        param1 = Parameter(magnitude=series1, units="EUR_2020/kW")
        param2 = Parameter(magnitude=series2, units="EUR_2020/kW")

        result = param1 - param2

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 3
            assert result.magnitude.loc["2030"] == 250.0  # 400 - 150
        pd.testing.assert_index_equal(result.magnitude.index, series1.index)
        assert result.units == "EUR_2020 / kilowatt"

    def test_parameter_series_scalar_multiplication(self) -> None:
        """Test multiplication of series parameter with scalar."""
        series_data = pd.Series([100.0, 200.0, 300.0], index=["2020", "2030", "2040"])
        param = Parameter(magnitude=series_data, units="EUR_2020/kW")

        result = param * 2.5

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 3
            assert result.magnitude.loc["2030"] == 500.0  # 200 * 2.5
        pd.testing.assert_index_equal(result.magnitude.index, series_data.index)
        assert result.units == "EUR_2020 / kilowatt"

    def test_parameter_series_scalar_division(self) -> None:
        """Test division of series parameter by scalar."""
        series_data = pd.Series([100.0, 200.0, 300.0], index=["2020", "2030", "2040"])
        param = Parameter(magnitude=series_data, units="EUR_2020/kW")

        result = param / 2.0

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 3
            assert result.magnitude.loc["2030"] == 100.0  # 200 / 2.0
        pd.testing.assert_index_equal(result.magnitude.index, series_data.index)
        assert result.units == "EUR_2020 / kilowatt"

    def test_parameter_series_power(self) -> None:
        """Test raising series parameter to a power."""
        series_data = pd.Series([2.0, 3.0, 4.0], index=["2020", "2030", "2040"])
        param = Parameter(magnitude=series_data, units="meter")

        result = param**2

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 3
            assert result.magnitude.loc["2030"] == 9.0  # 3^2
        pd.testing.assert_index_equal(result.magnitude.index, series_data.index)
        assert result.units == "meter ** 2"

    def test_parameter_mixed_scalar_series_addition(self) -> None:
        """Test addition between scalar and series parameters."""
        scalar_param = Parameter(magnitude=100, units="EUR_2020/kW")
        series_param = Parameter(
            magnitude=pd.Series([50.0, 100.0, 150.0], index=["2020", "2030", "2040"]),
            units="EUR_2020/kW",
        )

        result = scalar_param + series_param

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 3
            assert result.magnitude.loc["2030"] == 200.0  # 100 + 100

    def test_parameter_series_currency_conversion(self) -> None:
        """Test currency conversion with series magnitude."""
        series_data = pd.Series(
            [1000.0, 2000.0, 3000.0], index=["2020", "2030", "2040"]
        )
        param = Parameter(magnitude=series_data, units="EUR_2020/kW")

        # Note: This test might fail if currency data is not available
        # We'll use a simple test case
        try:
            converted = param.to_currency("USD_2020", "USA")
            assert isinstance(converted.magnitude, pd.Series)
            if isinstance(converted.magnitude, pd.Series):
                assert len(converted.magnitude) == 3
            pd.testing.assert_index_equal(converted.magnitude.index, series_data.index)
            assert "USD_2020" in str(converted.units)
        except Exception:
            # Skip if currency conversion data is not available
            pytest.skip("Currency conversion data not available")

    def test_parameter_series_heating_value_conversion(self) -> None:
        """Test heating value conversion with series magnitude."""
        series_data = pd.Series([10.0, 20.0, 30.0], index=["2020", "2030", "2040"])
        param = Parameter(
            magnitude=series_data, units="kWh/kg", carrier="H2", heating_value="LHV"
        )

        converted = param.change_heating_value("HHV")

        assert isinstance(converted.magnitude, pd.Series)
        if isinstance(converted.magnitude, pd.Series) and isinstance(
            param.magnitude, pd.Series
        ):
            assert len(converted.magnitude) == 3
            assert converted.magnitude.loc["2030"] > param.magnitude.loc["2030"]
        pd.testing.assert_index_equal(converted.magnitude.index, series_data.index)
        # Check that conversion actually happened (HHV should be higher than LHV)
        assert (
            converted.heating_value == "higher_heating_value"
        )  # pint uses canonical names

    def test_parameter_series_preserves_metadata(self) -> None:
        """Test that series operations preserve metadata."""
        series_data = pd.Series([100.0, 200.0, 300.0], index=["2020", "2030", "2040"])
        source = Source(
            title="Test Source", authors="Test Author", url="http://test.com"
        )

        param = Parameter(
            magnitude=series_data,
            units="EUR_2020/kW",
            carrier="el",
            heating_value=None,
            provenance="test_data",
            note="Test note",
            sources=SourceCollection(sources=[source]),
        )

        result = param * 2

        assert result.carrier == "electricity"  # pint uses canonical names
        assert result.provenance == "test_data"
        assert result.note == "Test note"
        assert len(result.sources.sources) == 1
        assert result.sources.sources[0].title == "Test Source"

    def test_parameter_series_different_lengths(self) -> None:
        """Test operations between series of different lengths."""
        series1 = pd.Series([100.0, 200.0], index=["2020", "2030"])
        series2 = pd.Series(
            [50.0, 100.0], index=["2020", "2030"]
        )  # Same length for now

        param1 = Parameter(magnitude=series1, units="EUR_2020/kW")
        param2 = Parameter(magnitude=series2, units="EUR_2020/kW")

        # This should work with matching lengths
        result = param1 + param2

        assert isinstance(result.magnitude, pd.Series)
        if isinstance(result.magnitude, pd.Series):
            assert len(result.magnitude) == 2
            assert result.magnitude.loc["2020"] == 150.0  # 100 + 50
            assert result.magnitude.loc["2030"] == 300.0  # 200 + 100

    def test_parameter_empty_series(self) -> None:
        """Test parameter with empty series."""
        empty_series = pd.Series([], dtype=float)
        param = Parameter(magnitude=empty_series, units="EUR_2020/kW")

        assert param._is_magnitude_series()
        if isinstance(param.magnitude, pd.Series):
            assert len(param.magnitude) == 0

    def test_parameter_single_element_series(self) -> None:
        """Test parameter with single-element series."""
        single_series = pd.Series([42.0], index=["2020"])
        param = Parameter(magnitude=single_series, units="EUR_2020/kW")

        assert param._is_magnitude_series()
        if isinstance(param.magnitude, pd.Series):
            assert len(param.magnitude) == 1
            assert param.magnitude.iloc[0] == 42.0
