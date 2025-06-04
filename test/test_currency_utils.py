"""Test the utility methods."""

import pathlib
import shutil
import sys
import warnings

import pandas as pd
import pytest

import technologydata as td

sys.path.append("./technology-data")
path_cwd = pathlib.Path.cwd()


@pytest.mark.parametrize(
    "input_string, expected_format, expected_result",
    [
        ("EUR-2025", r"^[A-Z]{3}-\d{4}$", "EUR-2025"),
        ("EU-2025", r"^[A-Z]{2}-\d{4}$", "EU-2025"),
        ("The currency unit is EU-2025", r"[A-Z]{3}-\d{4}", None),
        ("The currency unit is EUR-202", r"[A-Z]{3}-\d{4}", None),
        ("The currency unit is EUR-2025", r"[A-Z]{3}-\d{4}", "EUR-2025"),
        ("The currency unit is US-2025", r"[A-Z]{2}-\d{4}", "US-2025"),
    ],
)  # type: ignore
def test_ensure_currency_unit(
    input_string: str, expected_format: str, expected_result: str | None
) -> None:
    """Check if a currency unit follows the wished format."""
    assert (
        td.CurrencyUtils.ensure_currency_unit(input_string, expected_format)
        == expected_result
    )


@pytest.mark.parametrize(
    "input_string, new_currency_code, expected_format, expected_result",
    [
        ("EUR-2025", "USD", r"^[A-Z]{3}-\d{4}$", "USD-2025"),
        (
            "The currency unit is EUR-2025",
            "GPD",
            r"[A-Z]{3}-\d{4}",
            "The currency unit is GPD-2025",
        ),
        ("The currency unit", "USD", r"[A-Z]{3}-\d{4}", None),
        (12345, "USD", r"[A-Z]{3}-\d{4}", ValueError),
        ("The currency unit", 123, r"[A-Z]{3}-\d{4}", ValueError),
        ("The currency unit", "USD", 123, ValueError),
    ],
)  # type: ignore
def test_replace_currency_code(
    input_string: str,
    new_currency_code: str,
    expected_format: str,
    expected_result: str | None | ValueError,
) -> None:
    """Check if a currency unit is correctly replaced."""
    if isinstance(expected_result, type) and expected_result is ValueError:
        with pytest.raises(ValueError, match="Input must be a string."):
            td.CurrencyUtils.replace_currency_code(
                input_string, new_currency_code, expected_format
            )
    else:
        result = td.CurrencyUtils.replace_currency_code(
            input_string, new_currency_code, expected_format
        )
        assert result == expected_result


def test_convert_and_adjust_currency() -> None:
    """Check if a currency is converted and inflation adjusted correctly."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        data = {
            "region": ["FRA", "USA", "CAN", "ITA"],
            "unit": ["EUR-2020", "USD-2020", "CAD-2020", "MWh"],
            "value": [50.0, 100.0, 200.0, 300.0],
        }
        input_dataframe = pd.DataFrame(data)

        pydeflate_path = pathlib.Path(path_cwd, "pydeflate")

        # Create the folder
        pydeflate_path.mkdir(parents=True, exist_ok=True)

        new_dataframe = td.CurrencyUtils.convert_and_adjust_currency(
            2020,
            "imf_gdp_deflate",
            "USA",
            pathlib.Path(path_cwd, "pydeflate"),
            input_dataframe,
        )

        new_dataframe["value"] = new_dataframe["value"].astype(float).round(2)

        # Expected DataFrame (replace with the actual expected output)
        expected_data = {
            "region": ["FRA", "USA", "CAN", "ITA"],
            "unit": ["EUR-2020", "USD-2020", "CAD-2020", "MWh"],
            "value": [57.06, 100.00, 149.13, 300],
        }
        expected_df = pd.DataFrame(expected_data)

        if pydeflate_path.exists() and pydeflate_path.is_dir():
            shutil.rmtree(pydeflate_path)

        pd.testing.assert_frame_equal(new_dataframe, expected_df)
