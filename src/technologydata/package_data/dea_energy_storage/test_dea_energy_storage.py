# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the functions of the DEA energy storage parser."""

import typing

import pandas
import pytest

from technologydata.package_data.dea_energy_storage.dea_energy_storage import (
    clean_parameter_string,
    drop_invalid_rows,
    extract_year,
    format_val_number,
)


class TestDEAEnergyStorage:
    """Test suite for the functions of the DEA energy storage parser."""

    @pytest.mark.parametrize(
        "input_string, expected_string",
        [
            ("- Discharge efficiency [%]", "discharge efficiency"),
            ("Construction time [years]", "construction time"),
            ("- Another example [with brackets]", "another example"),
            ("No brackets or hyphen here", "no brackets or hyphen here"),
        ],
    )  # type: ignore
    def test_clean_parameter_string(
        self, input_string: str, expected_string: str
    ) -> None:
        """Check if the clean_parameter_string works as expected."""
        print(clean_parameter_string(input_string))
        assert clean_parameter_string(input_string) == expected_string

    def test_drop_invalid_rows(self) -> None:
        """Check if the drop_invalid_rows works as expected."""
        input_dataframe = pandas.DataFrame(
            {
                "Technology": ["AI", "", "ML", "new_tech", "Tech", "Tech_1", "Tech_2"],
                "par": ["p1", "p2", "", "p4", None, "p5", "p6"],
                "val": ["<1", "   ", None, "abc", "456", "456,1", "1,1x10^3"],
                "year": ["almost 2020", "2021", "2020", "2022", "", "2020", "2024"],
            }
        )
        expected_dataframe = pandas.DataFrame(
            {
                "Technology": ["AI", "Tech_1", "Tech_2"],
                "par": ["p1", "p5", "p6"],
                "val": ["<1", "456,1", "1,1x10^3"],
                "year": ["almost 2020", "2020", "2024"],
            }
        )
        output_dataframe = drop_invalid_rows(input_dataframe).reset_index(drop=True)
        comparison_df = output_dataframe.compare(expected_dataframe)
        assert comparison_df.empty

    @pytest.mark.parametrize(
        "input_year, expected_year",
        [
            ("some 1999", 1999),
            ("maybe 1", 1),
            ("1", 1),
            (12345, 12345),
        ],
    )  # type: ignore
    def test_extract_year(self, input_year: str, expected_year: int) -> None:
        """Check if extract_year works as expected, including exception handling."""
        result = extract_year(input_year)
        assert result == expected_year
        assert isinstance(result, int)

    @pytest.mark.parametrize(
        "input_number, expected_number",
        [
            ("1,1", 1.1),
            ("1", 1.0),
            ("1.3x10-23", 1.3e-23),
        ],
    )  # type: ignore
    def test_format_val_number(
        self, input_number: str, expected_number: int | None | typing.Any
    ) -> None:
        """Check if format_val_number works as expected, including exception handling."""
        result = format_val_number(input_number)
        assert isinstance(result, float)
        assert result == expected_number
