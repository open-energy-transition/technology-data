# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""TechnologyCollection class for representing an iterable of Technology Objects."""

import csv
import json
import logging
import pathlib
import re
from collections.abc import Iterator
from typing import Annotated, Self

import pandas
import pydantic

from technologydata.parameter import Parameter
from technologydata.technologies.growth_models import GrowthModel, LinearGrowth
from technologydata.technology import Technology

logger = logging.getLogger(__name__)


class TechnologyCollection(pydantic.BaseModel):  # type: ignore
    """
    Represent a collection of technologies.

    Attributes
    ----------
    technologies : List[Technology]
        List of Technology objects.

    """

    technologies: Annotated[
        list[Technology], pydantic.Field(description="List of Technology objects.")
    ]

    def __iter__(self) -> Iterator[Technology]:
        """
        Return an iterator over the list of Technology objects.

        Returns
        -------
        Iterator[Technology]
            An iterator over the Technology objects contained in the collection.

        """
        return iter(self.technologies)

    def __len__(self) -> int:
        """
        Return the number of technologies in this collection.

        Returns
        -------
        int
            The number of Technology objects in the technologies list.

        """
        return len(self.technologies)

    def get(
        self, name: str, region: str, year: int, case: str, detailed_technology: str
    ) -> Self:
        """
        Filter technologies based on regex patterns for non-optional attributes.

        Parameters
        ----------
        name : str
            Regex pattern to filter technology names.
        region : str
            Regex pattern to filter region identifiers.
        year : int
            Regex pattern to filter the year of the data.
        case : str
            Regex pattern to filter case or scenario identifiers.
        detailed_technology : str
            Regex pattern to filter detailed technology names.

        Returns
        -------
        TechnologyCollection
            A new TechnologyCollection with filtered technologies.

        """
        filtered_technologies = self.technologies

        if name is not None:
            pattern_name = re.compile(name, re.IGNORECASE)
            filtered_technologies = [
                t for t in filtered_technologies if pattern_name.search(t.name)
            ]

        if region is not None:
            pattern_region = re.compile(region, re.IGNORECASE)
            filtered_technologies = [
                t for t in filtered_technologies if pattern_region.search(t.region)
            ]

        if year is not None:
            pattern_year = re.compile(str(year), re.IGNORECASE)
            filtered_technologies = [
                t for t in filtered_technologies if pattern_year.search(str(t.year))
            ]

        if case is not None:
            pattern_case = re.compile(case, re.IGNORECASE)
            filtered_technologies = [
                t for t in filtered_technologies if pattern_case.search(t.case)
            ]

        if detailed_technology is not None:
            pattern_detailed_technology = re.compile(detailed_technology, re.IGNORECASE)
            filtered_technologies = [
                t
                for t in filtered_technologies
                if pattern_detailed_technology.search(t.detailed_technology)
            ]

        return TechnologyCollection(technologies=filtered_technologies)

    def to_dataframe(self) -> pandas.DataFrame:
        """
        Convert the TechnologyCollection to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the technology data.

        """
        return pandas.DataFrame(
            [technology.model_dump() for technology in self.technologies]
        )

    def to_csv(self, **kwargs: pathlib.Path | str | bool) -> None:
        """
        Export the TechnologyCollection to a CSV file.

        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments passed to pandas.DataFrame.to_csv().
            Common options include:
            - path_or_buf : str or pathlib.Path or file-like object, optional
                File path or object, if None, the result is returned as a string.
                Default is None.
            - sep : str
                String of length 1. Field delimiter for the output file.
                Default is ','.
            - index : bool
                Write row names (index). Default is True.
            - encoding : str
                String representing the encoding to use in the output file.
                Default is 'utf-8'.

        Notes
        -----
        The method converts the collection to a pandas DataFrame using
        `self.to_dataframe()` and then writes it to a CSV file using the provided
        kwargs.

        """
        default_kwargs = {
            "sep": ",",
            "index": False,
            "encoding": "utf-8",
            "quoting": csv.QUOTE_ALL,
        }

        # Merge default_kwargs with user-provided kwargs, giving precedence to user kwargs
        merged_kwargs = {**default_kwargs, **kwargs}
        output_dataframe = self.to_dataframe()
        output_dataframe.to_csv(**merged_kwargs)

    def to_json(
        self, file_path: pathlib.Path, schema_path: pathlib.Path | None = None
    ) -> None:
        """
        Export the TechnologyCollection to a JSON file, together with a data schema.

        Parameters
        ----------
        file_path : pathlib.Path
            The path to the JSON file to be created.
        schema_path : pathlib.Path
            The path to the JSON schema file to be created. By default, created with a `schema` suffix next to `file_path`.

        """
        if schema_path is None:
            schema_path = file_path.with_suffix(".schema.json")

        # Export the model's schema with descriptions to a dict
        schema = self.model_json_schema()

        # Save the schema (which includes descriptions) to a JSON file
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=4)

        with open(file_path, mode="w", encoding="utf-8") as jsonfile:
            json_data = self.model_dump_json(indent=4)  # Convert to JSON string
            jsonfile.write(json_data)

    @classmethod
    def from_json(cls, file_path: pathlib.Path | str) -> Self:
        """
        Load a TechnologyCollection instance from a JSON file.

        Parameters
        ----------
        file_path : pathlib.Path or str
            Path to the JSON file containing the data. Can be a pathlib.Path object or a string path.

        Returns
        -------
        TechnologyCollection
            An instance of TechnologyCollection initialized with the data from the JSON file.

        Raises
        ------
        TypeError
            If `file_path` is not a pathlib.Path or str.

        Notes
        -----
        This method reads the JSON data from the specified file, creates `Technology` objects
        for each item in the JSON list using `Technology.from_dict()`, and returns a new
        `TechnologyCollection` containing these objects.

        """
        if isinstance(file_path, pathlib.Path | str):
            file_path = pathlib.Path(file_path)
        else:
            raise TypeError("file_path must be a pathlib.Path or str")
        with open(file_path, encoding="utf-8") as jsonfile:
            json_data = json.load(jsonfile)
        techs = []
        for item in json_data:
            techs.append(Technology.from_dict(item))
        return cls(technologies=techs)

    def fit(
        self, parameter: str, model: GrowthModel, p0: dict[str, float] | None = None
    ) -> GrowthModel:
        """
        Fit a growth model to a specified parameter across all technologies in the collection.

        This method aggregates data points for the specified parameter from all technologies
        in the collection, adds them to the provided growth model, and fits the model using
        the initial parameter guesses provided in `p0`.

        Parameters
        ----------
        parameter : str
            The name of the parameter to fit the model to (e.g., "installed capacity").
        model : GrowthModel
            An instance of a growth model (e.g., LinearGrowth, ExponentialGrowth) to be fitted.
            May already be partially initialized with some parameters and/or data points.
        p0 : dict[str, float], optional
            Initial guess for the model parameters.

        Returns
        -------
        GrowthModel
            The fitted growth model with optimized parameters.

        Raises
        ------
        ValueError
            If the collection contains incompatible parameters with different units, heating values, or carriers.

        """
        first_param = None
        # Aggregate data points for the specified parameter from all technologies
        for tech in self.technologies:
            param = tech.parameters[parameter]
            if first_param is None:
                first_param = param

            try:
                first_param._check_parameter_compatibility(param)
            except ValueError as e:
                raise ValueError(
                    f"The collection contains one or more parameters with incompatible units/heating values/carriers:\n"
                    f"* {first_param}, and\n"
                    f"* {param}."
                ) from e

            model.add_data((tech.year, param.magnitude))

        # Fit the model using the provided initial parameter guesses
        model.fit(p0=p0)

        return model

    def project(
        self,
        to_years: list[int],
        parameter: str | None = None,
        model: GrowthModel | None = None,
        keep_remaining: bool | str = "closest",
        *,
        parameters: dict[str, GrowthModel | str] | None = None,
    ) -> Self:
        """
        Project specified parameters for all technologies in the collection to future years.

        This method uses the provided growth models to project the specified parameters
        for each technology in the collection to the given future years.
        Using the `keep_remaining` argument, the behavior on how to handle parameters
        without a provided model can be controlled.

        The method creates new Technology objects for each combination of original technology
        and future year, applying the appropriate growth model projections.

        Parameters
        ----------
        to_years : list[int]
            List of future years to which the parameters should be projected.
        keep_remaining : bool or str, default 'closest'
            Determines how to handle parameters without a provided model:
            - If False, these parameters are not included in the projected technologies.
            - If 'NaN', add the parameter with NaN values.
            - If 'mean', set their values to the mean of existing values in the collection.
            - If 'closest', set their values to the value of the closest year in the original data with
              a preference for past years if equidistant.
        parameter : str, optional
            The name of a single parameter to project (e.g., "installed capacity").
            If provided, `model` must also be provided.
            Cannot be used together with `parameters`.
        model : GrowthModel, optional
            An instance of a growth model (e.g., LinearGrowth, ExponentialGrowth) to be used
            for projecting the specified parameter. Must be provided if `parameter` is given.
            Cannot be used together with `parameters`.
        parameters : dict[str, GrowthModel], optional
            A dictionary mapping parameter names to their respective growth models for projection.
            If provided, `parameter` and `model` cannot be used.

        Returns
        -------
        TechnologyCollection
            A new TechnologyCollection with technologies projected to the specified future years.

        Raises
        ------
        ValueError
            If neither `parameter` and `model`, or `parameters` are not or all provided.

        """
        if parameters is None:
            if not parameter or not model:
                raise ValueError(
                    "(`parameters`) and (`parameter` and `model`) are mutually exclusive. At least one must be provided."
                )
            else:
                # Allow to specify a single parameter and model for convenience, but treat as dict internally
                parameters = {parameter: model}

        if keep_remaining in ["NaN", "mean"]:
            # find all parameters in the collection
            all_params: set[str] = set()
            for tech in self.technologies:
                all_params.update(tech.parameters.keys())

            remaining_params = all_params - set(parameters.keys())

            if keep_remaining == "mean":
                # Trick: A linear growth with m=0 should always return the mean of the provided data points
                parameters.update(
                    {param: LinearGrowth(m=0) for param in remaining_params}
                )

            elif keep_remaining == "NaN":
                # Add "NaN" for parameters without a provided model and handle those later
                parameters.update({param: "NaN" for param in remaining_params})
        elif not keep_remaining:
            # By default the remaining parameters are simply not included in the projected technologies
            pass
        elif keep_remaining == "closest":
            raise NotImplementedError("'closest' option not yet implemented.")  # TODO

        logger.debug(f"Projecting parameters as follows: {parameters}")

        projected_technologies = []
        for to_year in to_years:
            # Create a new Technology object for the projected year
            new_tech = Technology(
                name=self.technologies[0].name,
                region=self.technologies[0].region,
                year=to_year,
                case=self.technologies[0].case,
                detailed_technology=self.technologies[0].detailed_technology,
                parameters={},
            )

            for param, model in parameters.items():
                new_param: Parameter
                if isinstance(model, GrowthModel):
                    # Fit the model to the parameter data
                    model = self.fit(param, model.model_copy())

                    # Project the model to the specified future years
                    param_value = model.project(to_year)

                    logger.debug(
                        f"Resulting model for {param} in year {to_year}: {model}"
                    )
                    # Add the projected parameter to the new technology
                    new_param = (
                        self.technologies[0].parameters[param].model_copy(deep=True)
                    )
                    new_param.magnitude = param_value  # Set the projected value
                    new_param.provenance = f"Projected to {to_year} using {model}."
                    new_param.note = None  # Clear any existing note
                    new_param.sources = None  # Clear any existing sources

                elif model == "NaN":
                    new_param = Parameter(
                        magnitude=float("nan"),
                        note="Placeholder parameters with NaN value.",
                    )
                else:
                    raise ValueError(
                        f"Unexpected model type for parameter '{param}': {model}"
                    )

                new_tech.parameters[param] = new_param

            logger.debug(f"Projected technology for year {to_year}: {new_tech}")

            projected_technologies.append(new_tech)

        return TechnologyCollection(technologies=projected_technologies)
