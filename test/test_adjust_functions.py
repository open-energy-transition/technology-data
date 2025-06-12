"""Test functionality related to adjust_X functions in the Technologies class."""

import pathlib

import pytest

import technologydata as td


@pytest.mark.parametrize(
    "example_technologies",
    [
        {
            "technologies_name": "example01",
            "technologies_path": pathlib.Path(
                "technologydata", "datasources", "example01"
            ),
        },
        {
            "technologies_name": "example02",
            "technologies_path": pathlib.Path(
                "technologydata", "datasources", "example02"
            ),
        },
    ],
    indirect=True,
)  # type: ignore
def test_no_economies_of_scale(example_technologies: td.Technologies) -> None:
    """Without economies of scale the value should not change."""
    org_data = example_technologies.data.copy()

    # Get the adjusted data
    example_technologies.adjust_scale(
        new_scale=999,
        unit="MW",
        scaling_exponent=1,
    )
    adjusted_data = example_technologies.data["value"].copy()

    # Check if all values in adjusted_data are equal to the original values
    assert all(
        adjusted_value == original_value
        for adjusted_value, original_value in zip(adjusted_data, org_data["value"])
    ), "Scaling with exponent 1 should not change the value"


@pytest.mark.parametrize(
    "example_technologies",
    [
        {
            "technologies_name": "example01",
            "technologies_path": pathlib.Path(
                "technologydata", "datasources", "example01"
            ),
        },
        {
            "technologies_name": "example02",
            "technologies_path": pathlib.Path(
                "technologydata", "datasources", "example02"
            ),
        },
    ],
    indirect=True,
)  # type: ignore
def test_economies_of_scale(example_technologies: td.Technologies) -> None:
    """Test with common economies of scale with exponent 0.5."""
    org_data = example_technologies.data.copy()

    # Get the adjusted data
    example_technologies.adjust_scale(
        new_scale=2,
        unit="MW",
        scaling_exponent=0.5,
    )
    adjusted_data = example_technologies.data["value"].copy()

    # Calculate the expected values based on the scaling formula
    expected_values = org_data["value"] * (2 / org_data["scale"]) ** (0.5 - 1)

    # Check if all adjusted values are approximately equal to the expected values
    assert all(
        abs(adjusted_value - expected_value)
        < 1e-6  # Use a small tolerance for floating-point comparison
        for adjusted_value, expected_value in zip(adjusted_data, expected_values)
    ), "Scaling with exponent 0.5 should change the value to approx 0.7"


@pytest.mark.parametrize(
    "example_technologies",
    [
        {
            "technologies_name": "forecast01",
            "technologies_path": pathlib.Path(
                "test", "test_adjust_functions", "forecast01"
            ),
        }
    ],
    indirect=True,
)  # type: ignore
def test_adjust_year_linear_interpolation(
    example_technologies: td.Technologies,
) -> None:
    """Test linear forecasting through a middle value in 2025."""
    forecast = example_technologies.adjust_year(year=2025, model={"method": "linear"})

    assert forecast.shape[0] == 3, "Forecasted data missing additional row"
    assert forecast.iloc[1]["value"] == 150, (
        "Linear forecasted value for 2025 is incorrect"
    )


@pytest.mark.parametrize(
    "example_technologies",
    [
        {
            "technologies_name": "forecast01",
            "technologies_path": pathlib.Path(
                "test", "test_adjust_functions", "forecast01"
            ),
        }
    ],
    indirect=True,
)  # type: ignore
def test_adjust_year_linear_extrapolation(
    example_technologies: td.Technologies,
) -> None:
    """Test linear forecasting for a value outside the range of entries provided."""
    forecast = example_technologies.adjust_year(
        year=2040,
        model={
            "method": "linear",
            "order": 1,
            "limit_area": None,
            "limit_direction": "forward",
        },
    )

    assert forecast.shape[0] == 3, "Forecasted data missing additional row"
    assert forecast.iloc[2]["value"] == 200, (
        "Linear forecasted value for 2040 is incorrect and should be equal to the last support year value, i.e. 2030"
    )


# @pytest.mark.parametrize(
#     "example_technologies",
#     [
#         {
#             "technologies_name": "forecast01",
#             "technologies_path": pathlib.Path(
#                 "test", "test_adjust_functions", "currency_conversion01"
#             ),
#         }
#     ],
#     indirect=True,
# )  # type: ignore
# def test_adjust_currency(
#     example_technologies: td.Technologies,
# ) -> None:
#     """Test currency conversion and inflation adjustments."""
#     example_technologies.adjust_currency(
#         to_currency="USA-2020", source="International Monetary Fund"
#     )
#     example_technologies.to_csv(path="integrunittest.csv")
#    assert False
