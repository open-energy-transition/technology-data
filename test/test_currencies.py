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
        ("The currency unit is EUR-2025/kW_el", r"[A-Z]{3}-\d{4}", "EUR-2025"),
        ("The currency unit is US-2025", r"[A-Z]{2}-\d{4}", "US-2025"),
        ("USD_2025", r"[A-Z]{3}_\d{4}", "USD_2025"),
        ("USD_2025", r"[A-Z]{3}-\d{4}", None),
        (123, r"[A-Z]{3}-\d{4}", ValueError),
        (r"[A-Z]{3}-\d{4}", 123, ValueError),
    ],
)  # type: ignore
def test_extract_currency_unit(
    input_string: str, expected_format: str, expected_result: str | None | ValueError
) -> None:
    """Check if a currency unit follows the wished format."""
    if isinstance(expected_result, type) and expected_result is ValueError:
        with pytest.raises(ValueError, match="Input must be a string."):
            td.Currencies.extract_currency_unit(input_string, expected_format)
    else:
        assert (
            td.Currencies.extract_currency_unit(input_string, expected_format)
            == expected_result
        )


@pytest.mark.parametrize(
    "input_string, new_currency_code, new_currency_year, expected_format, expected_result, expected_exception_message",
    [
        ("EUR-2025", "USD", None, r"^[A-Z]{3}-\d{4}$", "USD-2025", None),
        ("EUR-2025", None, "2021", r"^[A-Z]{3}-\d{4}$", "EUR-2021", None),
        (
            "The currency unit is EUR-2025",
            "GPD",
            "2021",
            r"[A-Z]{3}-\d{4}",
            "The currency unit is GPD-2021",
            None,
        ),
        ("The currency unit", "USD", "2019", r"[A-Z]{3}-\d{4}", None, None),
        (
            12345,
            "USD",
            "2019",
            r"[A-Z]{3}-\d{4}",
            ValueError,
            "Input must be a string.",
        ),
        (
            "The currency unit",
            123,
            "2019",
            r"[A-Z]{3}-\d{4}",
            ValueError,
            "new_currency_code must be a string.",
        ),
        (
            "The currency unit",
            "USD",
            123,
            r"[A-Z]{3}-\d{4}",
            ValueError,
            "new_currency_year must be a string.",
        ),
        (
            "The currency unit",
            "USD",
            "2019",
            123,
            ValueError,
            "Input must be a string.",
        ),
    ],
)  # type: ignore
def test_update_currency_unit(
    input_string: str,
    new_currency_code: str,
    new_currency_year: str,
    expected_format: str,
    expected_result: str | None | ValueError,
    expected_exception_message: str | None,
) -> None:
    """Check if a currency unit is correctly replaced."""
    if isinstance(expected_result, type) and expected_result is ValueError:
        with pytest.raises(ValueError, match=expected_exception_message):
            td.Currencies.update_currency_unit(
                input_string, new_currency_code, new_currency_year, expected_format
            )
    else:
        result = td.Currencies.update_currency_unit(
            input_string, new_currency_code, new_currency_year, expected_format
        )
        assert result == expected_result


@pytest.mark.parametrize(
    "base_year_val, deflator_function_name, input_dataframe, target_currency, expected_result, expected_exception_message",
    [
        (
            2020,
            "international_monetary_fund",
            pd.DataFrame(
                {
                    "region": ["FRA", "USA", "CAN", "ITA"],
                    "unit": ["EUR-2020/MWh_el", "USD-2020", "CAD-2020", "MWh"],
                    "value": [50.0, 100.0, 200.0, 300.0],
                }
            ),
            "USA",
            pd.DataFrame(
                {
                    "region": ["FRA", "USA", "CAN", "ITA"],
                    "unit": ["USD-2020/MWh_el", "USD-2020", "USD-2020", "MWh"],
                    "value": [57.06, 100.00, 149.13, 300],
                }
            ),
            None,
        ),
        (
            2020,
            "international_monetary_fund",
            pd.DataFrame(
                {
                    "region": ["FRA", "USA", "CAN", "ITA"],
                    "unit": ["EUR-2015/MWh_el", "USD-2015", "CAD-2015", "MWh"],
                    "value": [50.0, 100.0, 200.0, 300.0],
                }
            ),
            None,
            pd.DataFrame(
                {
                    "region": ["FRA", "USA", "CAN", "ITA"],
                    "unit": ["EUR-2015/MWh_el", "USD-2015", "CAD-2015", "MWh"],
                    "value": [53.33, 108.27, 215.56, 300],
                }
            ),
            None,
        ),
        (
            2020,
            "international_monetary_fund",
            pd.DataFrame(
                {
                    "unit": ["EUR-2015/MWh_el", "USD-2015", "CAD-2015", "MWh"],
                    "value": [50.0, 100.0, 200.0, 300.0],
                }
            ),
            None,
            ValueError,
            "Input dataFrame is missing required columns:",
        ),
        (
            2020,
            "random_deflate",
            pd.DataFrame(
                {
                    "region": ["FRA", "USA", "CAN", "ITA"],
                    "unit": ["EUR-2020/MWh_el", "USD-2020", "CAD-2020", "MWh"],
                    "value": [50.0, 100.0, 200.0, 300.0],
                }
            ),
            "USA",
            ValueError,
            "Deflator function 'random_deflate' not found in registry",
        ),
    ],
)  # type: ignore
def test_adjust_currency(
    base_year_val: int,
    deflator_function_name: str,
    input_dataframe: pd.DataFrame,
    target_currency: str,
    expected_result: pd.DataFrame | ValueError,
    expected_exception_message: str | None,
) -> None:
    """Check if currency conversion and inflation adjustment work correctly."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        pydeflate_path = pathlib.Path(path_cwd, "pydeflate")

        if isinstance(expected_result, type) and expected_result is ValueError:
            with pytest.raises(ValueError, match=expected_exception_message):
                td.Currencies.adjust_currency(
                    base_year_val,
                    target_currency,
                    input_dataframe,
                    deflator_function_name,
                )
        else:
            # Create the folder if needed
            pydeflate_path.mkdir(parents=True, exist_ok=True)

            # Assume td.CurrencyUtils is imported in the test context
            new_dataframe = td.Currencies.adjust_currency(
                base_year_val,
                target_currency,
                input_dataframe,
                deflator_function_name,
                pydeflate_path,
            )

            new_dataframe["value"] = new_dataframe["value"].astype(float).round(2)
            if pydeflate_path.exists() and pydeflate_path.is_dir():
                shutil.rmtree(pydeflate_path)

            pd.testing.assert_frame_equal(new_dataframe, expected_result)
