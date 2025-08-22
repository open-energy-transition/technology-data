# SPDX-FileCopyrightText: 2025 The technology-data authors
#
# SPDX-License-Identifier: MIT

import logging
from abc import abstractmethod
from typing import Annotated

from pydantic import BaseModel, Field

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
    def project(
        self, technologies: Technology | TechnologyCollection
    ) -> TechnologyCollection:
        """Project values for a Technology or TechnologyCollection using the requested growth model."""
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
        assert isinstance(technologies, Technology), (
            "`technologies` must be a Technology instance."
        )

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
                param.magnitude *= growth_factor
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


def project_with_model(
    tech: Technology,
    model: str | GrowthModel,
    **kwargs,
) -> TechnologyCollection:
    """
    Project a Technology or TechnologyCollection using the specified GrowthModel.

    Returns a new TechnologyCollection with projected values.
    """
    if isinstance(model, str):
        if model in ["LinearGrowth", "linear"]:
            model = LinearGrowth(**kwargs)
        else:
            raise ValueError(f"Unknown growth model: {model}")

    return model.project(tech)
