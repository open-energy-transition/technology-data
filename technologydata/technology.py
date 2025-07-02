"""
Technology class for representing a technology with parameters and transformation methods.

Examples
--------
>>> from technologydata.parameter import Parameter
>>> from technologydata.unit_value import UnitValue
>>> from technologydata.source import Source
>>> src = Source(name="Example Source", url="http://example.com")
>>> param = Parameter(quantity=UnitValue(value=1000, unit="EUR_2020/kW"), sources=[src])
>>> tech = Technology(
...     name="Electrolyzer",
...     region="EU",
...     year=2025,
...     parameters={"specific_investment": param}
... )

"""

from typing import Any

from pydantic import BaseModel, Field

from technologydata.parameter import Parameter


class Technology(BaseModel):
    """
    Represents a technology with region, year, and a flexible set of parameters.

    Parameters
    ----------
    name : str
        Name of the technology.
    region : Optional[str]
        Region identifier.
    year : Optional[int]
        Year of the data.
    parameters : Dict[str, Parameter]
        Dictionary of parameter names to Parameter objects.
    case : Optional[str]
        Case or scenario identifier.
    detailed_technology : Optional[str]
        More detailed technology name.

    Attributes
    ----------
    name : str
        Name of the technology.
    region : Optional[str]
        Region identifier.
    year : Optional[int]
        Year of the data.
    parameters : Dict[str, Parameter]
        Dictionary of parameter names to Parameter objects.
    case : Optional[str]
        Case or scenario identifier.
    detailed_technology : Optional[str]
        More detailed technology name.

    """

    name: str = Field(..., description="Name of the technology.")
    region: str | None = Field(None, description="Region identifier.")
    year: int | None = Field(None, description="Year of the data.")
    parameters: dict[str, Parameter] = Field(
        default_factory=dict, description="Parameters."
    )
    case: str | None = Field(None, description="Case or scenario identifier.")
    detailed_technology: str | None = Field(
        None, description="Detailed technology name."
    )

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

    def check_consistency(self) -> bool:
        """
        Check for consistency and completeness of parameters.

        Returns
        -------
        bool
            True if consistent, False otherwise.

        """
        # Example: check required parameters
        required = ["specific_investment", "investment", "lifetime"]
        missing = [p for p in required if p not in self.parameters]
        return len(missing) == 0

    def calculate_parameters(self, parameters: Any | None = None) -> "Technology":
        """
        Calculate missing or derived parameters.

        Parameters
        ----------
        parameters : Optional[Any]
            List of parameter names to calculate, or "<missing>" for all missing.

        Returns
        -------
        Technology
            A new Technology object with calculated parameters.

        """
        # Placeholder: implement calculation logic as needed
        return self

    def adjust_currency(self, target_currency: str) -> "Technology":
        """
        Adjust all currency parameters to a target currency.

        Parameters
        ----------
        target_currency : str
            The target currency (e.g., 'EUR_2020').

        Returns
        -------
        Technology
            A new Technology object with adjusted currency.

        """
        # Placeholder: implement currency adjustment logic
        return self

    def adjust_region(self, target_region: str) -> "Technology":
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

    def adjust_scale(self, scaling_factor: float) -> "Technology":
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
