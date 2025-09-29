# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the functions of the DEA energy storage parser."""

import pandas
import pytest

from technologydata.package_data.dea_energy_storage.dea_energy_storage import (
    clean_parameter_string,
    drop_invalid_rows,
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
                "Technology": ["AI", None, "", "ML", "new_tech"],
                "par": ["par1", "par2", "par3", "par4", "par5"],
                "year": ["2020", "2020", "", "abc", ""],
                "val": ["123.2", "123,2", ]
            }
        )
        expected_dataframe = pandas.DataFrame(
            {
                "Technology": ["AI"],
                "par": ["par1"],
                "year": ["2020"],
            }
        )
        output_dataframe = drop_invalid_rows(input_dataframe)
        comparison_df = output_dataframe.compare(expected_dataframe)
        assert comparison_df.empty
