# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Technology class for representing a technology with parameters and transformation methods."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Literal, Self

import pydantic

from technologydata.parameter import Parameter

if TYPE_CHECKING:
    from technologydata.equations import EquationRegistry

ConsistencyStatus = bool | Literal["missing parameters", "inapplicable"]


class Technology(pydantic.BaseModel):
    """
    Represent a technology with region, year, and a flexible set of parameters.

    Attributes
    ----------
    name : str
        Name of the technology.
    detailed_technology : str
        More detailed technology name.
    case : str
        Case or scenario identifier.
    region : str
        Region identifier.
    year : int
        Year of the data.
    parameters : Dict[str, Parameter]
        Dictionary of parameter names to Parameter objects.

    """

    name: Annotated[str, pydantic.Field(description="Name of the technology.")]
    detailed_technology: Annotated[
        str, pydantic.Field(description="Detailed technology name.")
    ]
    case: Annotated[str, pydantic.Field(description="Case or scenario identifier.")]
    region: Annotated[str, pydantic.Field(description="Region identifier.")]
    year: Annotated[int, pydantic.Field(description="Year of the data.")]
    parameters: Annotated[
        dict[str, Parameter],
        pydantic.Field(default_factory=dict, description="Parameters."),
    ]

    def __getitem__(self, key: str) -> Parameter:
        """
        Access a parameter by name.

        Parameters
        ----------
        key : str
            Parameter name.

        Returns
        -------
        Parameter
            The requested parameter.

        """
        return self.parameters[key]

    def __setitem__(self, key: str, value: Parameter) -> None:
        """
        Set a parameter by name.

        Parameters
        ----------
        key : str
            Parameter name.
        value : Parameter
            The parameter to set.

        """
        self.parameters[key] = value

    def check_consistency(
        self,
        parameters: Sequence[str] | None = None,
        equations: "EquationRegistry | None" = None,
        rtol: float = 1e-6,
        atol: float = 1e-9,
    ) -> dict[str, ConsistencyStatus]:
        """
        Check equation-level consistency for selected parameters.

        If ``parameters`` is given, only equations linked to those parameters
        are checked and other parameters are ignored. If ``parameters`` is
        ``None``, all parameters present on this technology are checked.

        If ``equations`` is not provided, the package default registry
        is used.

        Returns a mapping from equation name to status:

        - ``True`` if values are consistent with the equation.
        - ``False`` if values violate the equation.
        - ``"missing parameters"`` if some required equation parameters are
          present but not all.
        - ``"inapplicable"`` if none of the equation parameters are present.

        Returns
        -------
        dict[str, ConsistencyStatus]
            Consistency status per checked equation.

        """
        if equations is None:
            from technologydata.default_equations import equation_registry as default_registry

            equations = default_registry

        checked_names = tuple(parameters or self.parameters.keys())
        checked_set = set(checked_names)

        # Keep one anchor target parameter per equation so each equation is
        # evaluated exactly once while still respecting the user's filter.
        equations_to_check: dict[str, tuple[object, str]] = {}
        for target in checked_names:
            for equation in equations._equations_by_parameter.get(target, []):
                if equation.name not in equations_to_check:
                    equations_to_check[equation.name] = (equation, target)

        available_params = dict(self.parameters)

        result: dict[str, ConsistencyStatus] = {}
        for equation_name, (equation, target) in equations_to_check.items():
            present_count = sum(1 for name in equation.parameters if name in available_params)

            if present_count == 0:
                result[equation_name] = "inapplicable"
                continue

            if present_count < len(equation.parameters):
                result[equation_name] = "missing parameters"
                continue

            if target not in available_params:
                result[equation_name] = "missing parameters"
                continue

            known_params = {
                name: available_params[name]
                for name in equation.parameters
                if name != target
            }

            try:
                expected = equations.calculate(
                    target,
                    known_params,
                    equation_name=equation_name,
                )
            except Exception:
                result[equation_name] = False
                continue

            observed = available_params[target]
            result[equation_name] = observed.isclose(
                expected,
                rtol=rtol,
                atol=atol,
            )

        return result

    def calculate_parameters(
        self,
        targets: str | list[str] | None = None,
        equation_names: dict[str, str] | None = None,
    ) -> Self:
        """
        Derive missing parameters using registered equations.

        Parameters
        ----------
        targets : str or list of str, optional
            Parameter names to derive. If ``None``, all parameters that can be
            derived from currently available parameters (and are not already
            present) are calculated automatically.
        equation_names : dict of str to str, optional
            Mapping of parameter name to equation name, used to override the
            default equation for specific targets
            (e.g. ``{"eac": "eac_simple"}``).

        Returns
        -------
        Technology
            A new Technology instance with the derived parameters added.

        Raises
        ------
        ValueError
            If a requested target has no applicable equation, required parameters
            are missing, or input currencies are inconsistent.

        """
        from technologydata.default_equations import equation_registry

        new_params: dict[str, Parameter] = dict(self.parameters)

        if targets is None:
            targets = [
                p
                for p in equation_registry._equations_by_parameter
                if p not in new_params
                and equation_registry.can_calculate(p, new_params)
            ]
        elif isinstance(targets, str):
            targets = [targets]

        for target in targets:
            equation_name = equation_names.get(target) if equation_names else None
            new_params[target] = equation_registry.calculate(
                target, new_params, equation_name
            )

        return self.model_copy(update={"parameters": new_params})

    def to_currency(
        self,
        target_currency: str,
        overwrite_country: None | str = None,
        source: str = "worldbank",
    ) -> Self:
        """
        Adjust the currency of all parameters of the technology to the target currency.

        The conversion includes inflation and exchange rates based on the object's region.
        If a different country should be used for inflation adjustment, use `overwrite_country`.

        Parameters
        ----------
        target_currency : str
            The target currency (e.g., 'EUR_2020').
        overwrite_country : str, optional
            ISO 3166 alpha-3 country code to use for inflation adjustment instead of the object's region.
        source: str, optional
            The source of the inflation data, either "worldbank"/"wb" or "international_monetary_fund"/"imf".
            Defaults to "worldbank".
            Depending on the source, different years to adjust for inflation may be available.

        Returns
        -------
        Technology
            A new Technology object with all its parameters adjusted to the target currency.

        """
        country = self.region
        if overwrite_country:
            country = overwrite_country

        # Copy the Technology object
        new_tech: Self = self.model_copy(deep=True)

        # Iterate over parameters and convert their currency
        for name, param in new_tech.parameters.items():
            new_tech.parameters[name] = param.to_currency(
                target_currency=target_currency,
                country=country,
                source=source,
            )

        return new_tech

    def adjust_region(self, target_region: str) -> Self:
        """
        Adjust technology parameters to match a different region.

        Parameters
        ----------
        target_region : str
            The target region.

        Returns
        -------
        Technology
            A new Technology object with adjusted region.

        """
        # Placeholder: implement region adjustment logic
        return self

    def adjust_scale(self, scaling_factor: float) -> Self:
        """
        Scale parameter values by a scaling factor.

        Parameters
        ----------
        scaling_factor : float
            The scaling factor to apply.

        Returns
        -------
        Technology
            A new Technology object with scaled parameters.

        """
        # Placeholder: implement scaling logic
        return self
