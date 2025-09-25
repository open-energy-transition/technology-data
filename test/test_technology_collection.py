# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the initialization and methods of the TechnologyCollection class."""

import pathlib

import pandas
import pytest

import technologydata

path_cwd = pathlib.Path.cwd()


class TestTechnologyCollection:
    """Test suite for the TechnologyCollection class in the technologydata module."""

    def test_to_csv(self) -> None:
        """Check if the example technology collection is exported to CSV."""
        input_file = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "solar_photovoltaics_example_03",
            "technologies.json",
        )
        technology_collection = technologydata.TechnologyCollection.from_json(
            input_file
        )
        output_file = pathlib.Path(path_cwd, "technologies.csv")
        technology_collection.to_csv(path_or_buf=output_file)
        assert output_file.is_file()
        output_file.unlink(missing_ok=True)

    def test_to_dataframe(self) -> None:
        """Check if the example technology collection is exported to pandas dataframe."""
        input_file = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "solar_photovoltaics_example_03",
            "technologies.json",
        )
        technology_collection = technologydata.TechnologyCollection.from_json(
            input_file
        )
        assert isinstance(technology_collection.to_dataframe(), pandas.DataFrame)

    def test_to_json(self) -> None:
        """Check if the example technology collection is exported to JSON."""
        input_file = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "solar_photovoltaics_example_03",
            "technologies.json",
        )
        technology_collection = technologydata.TechnologyCollection.from_json(
            input_file
        )
        output_file = pathlib.Path(path_cwd, "technologies.json")
        schema_file = pathlib.Path(path_cwd, "technologies.schema.json")
        technology_collection.to_json(pathlib.Path(output_file))
        assert output_file.is_file()
        assert schema_file.is_file()
        output_file.unlink(missing_ok=True)
        schema_file.unlink(missing_ok=True)

    def test_from_json(self) -> None:
        """Check if the example technology collection is imported from JSON."""
        input_file = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "solar_photovoltaics_example_03",
            "technologies.json",
        )
        technology_collection = technologydata.TechnologyCollection.from_json(
            input_file
        )
        assert isinstance(technology_collection, technologydata.TechnologyCollection)
        assert len(technology_collection) == 2

    @pytest.mark.parametrize(
        "name, region, year, case, detailed_technology",
        [
            ["Solar photovoltaics", "DEU", 2022, "example-scenario", "Si-HC"],
            ["Solar photovoltaics", "DEU", 2022, "example-project", "Si-HC"],
        ],
    )  # type: ignore
    def test_get(
        self, name: str, region: str, year: int, case: str, detailed_technology: str
    ) -> None:
        """Check if the example technology collection is filtered as requested."""
        input_file = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "solar_photovoltaics_example_03",
            "technologies.json",
        )
        technologies_collection = technologydata.TechnologyCollection.from_json(
            input_file
        )
        result = technologies_collection.get(
            name=name,
            region=region,
            year=year,
            case=case,
            detailed_technology=detailed_technology,
        )
        assert isinstance(result, technologydata.TechnologyCollection)
        assert len(result.technologies) == 1

    def test_fit_linear_growth(self) -> None:
        """Test TechnologyCollection.fit with LinearGrowth model."""
        tech = technologydata.Technology(
            name="Amazing technology",
            detailed_technology="",
            region="",
            case="",
            year=2020,
            parameters={
                "total units": technologydata.Parameter(magnitude=2020),
            },
        )

        tc = technologydata.TechnologyCollection(
            technologies=[
                tech,
                tech.model_copy(
                    deep=True,
                    update={
                        "year": 2030,
                        "parameters": {
                            "total units": technologydata.Parameter(magnitude=2030),
                        },
                    },
                ),
            ]
        )

        # Fit 'total units' parameter with LinearGrowth
        from technologydata.technologies.growth_models import LinearGrowth

        model = LinearGrowth()
        fitted = tc.fit("total units", model)
        assert isinstance(fitted, LinearGrowth)
        assert pytest.approx(fitted.m) == 1
        assert pytest.approx(fitted.A) == 0

    def test_project_linear_growth(self) -> None:
        """Test TechnologyCollection.project with LinearGrowth model."""
        input_file = pathlib.Path(
            path_cwd,
            "test",
            "test_data",
            "solar_photovoltaics_example_03",
            "technologies.json",
        )
        tc = technologydata.TechnologyCollection.from_json(input_file)
        from technologydata.technologies.growth_models import LinearGrowth

        projected_tc = tc.project(
            to_years=[2030],
            parameters={"capacity": LinearGrowth()},
        )
        assert isinstance(projected_tc, technologydata.TechnologyCollection)
        assert projected_tc.technologies[0].year == 2030
        assert "capacity" in projected_tc.technologies[0].parameters
        assert isinstance(
            projected_tc.technologies[0].parameters["capacity"].magnitude, float
        )

        # non-projected parameters should not be present
        assert "investment" not in projected_tc.technologies[0].parameters

    def test_project_other_parameter_options(self) -> None:
        """Test projection of parameters using 'mean', 'closest', and 'NaN' options."""
        tech = technologydata.Technology(
            name="Amazing technology",
            detailed_technology="",
            region="",
            case="",
            year=2020,
            parameters={
                "total units": technologydata.Parameter(magnitude=2000),
            },
        )

        tc = technologydata.TechnologyCollection(
            technologies=[
                tech,
                tech.model_copy(
                    deep=True,
                    update={
                        "year": 2030,
                        "parameters": {
                            "total units": technologydata.Parameter(magnitude=3000),
                        },
                    },
                ),
            ]
        )

        ptc = tc.project(
            to_years=[2025],
            parameters={
                "total units": "mean",
            },
        )

        assert (
            pytest.approx(
                (
                    tc.technologies[0].parameters["total units"].magnitude
                    + tc.technologies[1].parameters["total units"].magnitude
                )
                / 2,
            )
            == ptc.technologies[0].parameters["total units"].magnitude
        )

        ptc = tc.project(
            to_years=[2025],
            parameters={
                "total units": "NaN",
            },
        )

        assert pandas.isna(ptc.technologies[0].parameters["total units"].magnitude)

        # "closest" currently raises NotImplementedError
        with pytest.raises(NotImplementedError):
            _ = tc.project(
                to_years=[2025],
                parameters={
                    "total units": "closest",
                },
            )
