# SPDX-FileCopyrightText: 2025 The technology-data authors
#
# SPDX-License-Identifier: MIT
"""Growth models for projecting technology parameters over time."""

import logging
from abc import abstractmethod
from typing import Annotated, Self

import numpy as np
from pydantic import BaseModel, Field, model_validator

from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

logger = logging.getLogger(__name__)


class GrowthModel(BaseModel):
    """Abstract base for growth models used in projections."""

    affected_parameters: Annotated[
        list[str],
        Field(description="Parameters that will be modified by the model."),
    ]
    to_years: Annotated[list[int], Field(description="Years to project to.")]

    @abstractmethod
    def project(self, technologies: Technology) -> TechnologyCollection:
        """Project values for a Technology using the requested growth model."""
        pass


class LinearGrowth(GrowthModel):
    """Project with linear growth model."""

    annual_growth_rate: Annotated[
        float, Field(description="Annual growth rate for the projection")
    ]

    def project(
        self,
        technologies: Technology,
    ) -> TechnologyCollection:
        """
        Project specified parameters for each group in the TechnologyCollection for the given years.

        Only operates on parameters present in the technology and those that are specified in affected_parameters of the model.

        Parameters
        ----------
        technologies : Technology
            The Technology instance used as the basis for projection.

        Returns
        -------
        TechnologyCollection
            A new TechnologyCollection with the original and projected technologies for the years the model was build for.

        """
        new_techs = []

        for to_year in self.to_years:
            # For each year, create a copy of the technology to modify it with the projected values
            new_tech = technologies.model_copy(deep=True)
            new_tech.year = to_year

            for affected_parameter in self.affected_parameters:
                if affected_parameter not in new_tech.parameters:
                    logger.debug(
                        f"Parameter {affected_parameter} not in technology. Available parameters: {new_tech.parameters.keys()}. Skipping."
                    )
                    continue

                param = new_tech.parameters[affected_parameter]
                growth_factor = 1 + self.annual_growth_rate * (
                    to_year - technologies.year
                )
                param.magnitude *= growth_factor  # TODO remove 'magnitude' here when scalar operations on Parameter are supported
                if param.provenance is None:
                    param.provenance = ""
                param.provenance = f" Increased by {self.annual_growth_rate * 100}% per year from {technologies.year} to {to_year} for a total growth factor of {growth_factor}."

                new_tech[affected_parameter] = param

            new_techs.append(new_tech)

        # Return a new TechnologyCollection with the original and projected technologies
        return TechnologyCollection(technologies=[technologies] + new_techs)

    # * Define which parameters this operates on and modifies
    # * Define how it modifies these parameters
    # * When LinearGrowth is initialised, provide the parameters it operates on (installed capacity, capacity) and the annual growth rate
    # * Operate on the parameters if they are present, ignore them if not
    # * when calling project, specify the years to project to
    # * group the technologycollection by name, region, year, parameters, case, detailed_technology and project for each group
    # * make the abstract class inherit from pydantic.BaseModel for validation


class ExponentialGrowth(GrowthModel):
    """Project with exponential growth model."""

    growth_rate: Annotated[
        float,
        Field(
            description="Growth rate (based on an annual time constant) for the projection"
        ),
    ]

    def project(
        self,
        technologies: Technology,
    ) -> TechnologyCollection:
        """
        Project specified parameters for each group in the TechnologyCollection for the given years.

        Only operates on parameters present in the technology and those that are specified in affected_parameters of the model.

        Parameters
        ----------
        technologies : Technology
            The Technology instance used as the basis for projection.

        Returns
        -------
        TechnologyCollection
            A new TechnologyCollection with the original and projected technologies for the years the model was build for.

        """
        new_techs = []

        for to_year in self.to_years:
            # For each year, create a copy of the technology to modify it with the projected values
            new_tech = technologies.model_copy(deep=True)
            new_tech.year = to_year

            for affected_parameter in self.affected_parameters:
                if affected_parameter not in new_tech.parameters:
                    logger.debug(
                        f"Parameter {affected_parameter} not in technology. Available parameters: {new_tech.parameters.keys()}. Skipping."
                    )
                    continue

                param = new_tech.parameters[affected_parameter]
                growth_factor = (1 + self.growth_rate) ** (to_year - technologies.year)
                param.magnitude *= growth_factor  # TODO remove 'magnitude' here when scalar operations on Parameter are supported
                if param.provenance is None:
                    param.provenance = ""
                param.provenance = f" Increased by {self.growth_rate * 100}% per year from {technologies.year} to {to_year} for a total growth factor of {growth_factor}."

                new_tech[affected_parameter] = param

            new_techs.append(new_tech)

        # Return a new TechnologyCollection with the original and projected technologies
        return TechnologyCollection(technologies=[technologies] + new_techs)


class LogisticGrowth(GrowthModel):
    """Project with a logistic growth model."""

    logistic_growth_rate: Annotated[
        float | None,
        Field(
            default=None,
            description="Logistic growth rate (based on an annual time constant) for the projection. Must provide exactly two of the three: logistic_growth_rate, carrying_capacity, midpoint_year.",
        ),
    ]
    carrying_capacity: Annotated[
        float | None,
        Field(
            default=None,
            description="Carrying capacity for the logistic growth model, representing the maximum achievable value. Must provide exactly two of the three: logistic_growth_rate, carrying_capacity, midpoint_year.",
        ),
    ]
    midpoint_year: Annotated[
        int | None,
        Field(
            default=None,
            description="The year at which the growth rate is at its maximum (inflection point of the logistic curve). Must provide exactly two of the three: logistic_growth_rate, carrying_capacity, midpoint_year.",
        ),
    ]

    class Config:
        """Pydantic configuration for the LogisticGrowth model."""

        validate_assignment = True

    @model_validator(mode="after")
    def check_overspecification(self) -> Self:
        """Ensure the model is not overspecified by providing exactly two of the three model parameters."""
        if (
            sum(
                v is not None
                for v in [
                    self.logistic_growth_rate,
                    self.carrying_capacity,
                    self.midpoint_year,
                ]
            )
            != 2
        ):
            raise ValueError(
                "Model is overspecified. "
                "Only two of logistic_growth_rate, carrying_capacity, and midpoint_year can be provided."
            )
        return self

    def project(
        self,
        technologies: Technology,
    ) -> TechnologyCollection:
        """
        Project specified parameters for each group in the TechnologyCollection for the given years using a logistic growth model.

        The user must provide exactly two of the three: logistic_growth_rate, carrying_capacity, midpoint_year.
        The third is computed so that the curve passes through the initial value at the technology's year.
        """
        new_techs = []

        for to_year in self.to_years:
            new_tech = technologies.model_copy(deep=True)
            new_tech.year = to_year

            for affected_parameter in self.affected_parameters:
                if affected_parameter not in new_tech.parameters:
                    logger.debug(
                        f"Parameter {affected_parameter} not in technology. Available parameters: {new_tech.parameters.keys()}. Skipping."
                    )
                    continue

                # Calculate the missing parameter for the model based on the
                # parameter value/technology year and the provided two growth parameters
                param = new_tech.parameters[affected_parameter]

                tinit = technologies.year
                Linit = technologies.parameters[affected_parameter].magnitude

                t0 = self.midpoint_year
                L = self.carrying_capacity
                r = self.logistic_growth_rate

                if Linit <= 0:
                    raise ValueError(
                        f"Initial value for parameter {affected_parameter} must be positive for logistic growth projection."
                    )
                if L is not None and Linit >= L:
                    raise ValueError(
                        f"Initial value for parameter {affected_parameter} must be less than carrying_capacity for logistic growth projection."
                    )

                # midpoint_year from carrying_capacity and logistic_growth_rate (t0 from L and r)
                if L and r:
                    t0 = tinit - np.log(L / Linit - 1) / r

                    if t0 <= tinit:
                        raise ValueError(
                            f"Calculated midpoint_year {t0} is not after initial year {tinit}. Check carrying_capacity and logistic_growth_rate values."
                        )

                # logistic_growth_rate from carrying_capacity and midpoint_year (r from L and t0)
                if L and t0:
                    r = (-1) * np.log(L - Linit) / (tinit - t0)

                    if r <= 0:
                        raise ValueError(
                            f"Calculated logistic_growth_rate {r} is not positive. Check carrying_capacity and midpoint_year values."
                        )

                # carrying_capacity from logistic_growth_rate and midpoint_year (L from r and t0)
                if r and t0:
                    L = Linit * (1 + np.exp(-r * (tinit - t0)))

                    if L <= Linit:
                        raise ValueError(
                            f"Calculated carrying_capacity {L} is not greater than initial value {Linit}. Check logistic_growth_rate and midpoint_year values."
                        )

                # Now use the standard logistic formula
                projected = L / (1 + np.exp(-r * (to_year - t0)))

                param.magnitude = projected
                if param.provenance is None:
                    param.provenance = ""
                param.provenance = (
                    f" Projected using logistic growth from {tinit} "
                    "with initial_value {Linit}) "
                    "to year={to_year} "
                    "with carrying_capacity={L}, "
                    "logistic_growth_rate={r}, "
                    "midpoint_year={t0}."
                )
                new_tech[affected_parameter] = param

            new_techs.append(new_tech)

        return TechnologyCollection(technologies=[technologies] + new_techs)


def project_with_model(
    tech: Technology,
    model: str | GrowthModel,
    **kwargs: dict[str, list[str] | float | list[int]],
) -> TechnologyCollection:
    """
    Project a Technology or TechnologyCollection using the specified GrowthModel.

    Returns a new TechnologyCollection with projected values.
    """
    if isinstance(model, str):
        if model in ["LinearGrowth", "linear"]:
            model = LinearGrowth(**kwargs)
        elif model in ["ExponentialGrowth", "exponential"]:
            model = ExponentialGrowth(**kwargs)
        else:
            raise ValueError(f"Unknown growth model: {model}")

    return model.project(tech)
