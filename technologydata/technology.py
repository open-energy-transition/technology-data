# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT


# TODO replaceholder

"""Technology class for representing a technology with parameters and transformation methods."""

import logging
import typing

import pydantic

from technologydata.parameter import Parameter

logger = logging.getLogger(__name__)


def make_hashable(value):
    if isinstance(value, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, set):
        return tuple(sorted(make_hashable(v) for v in value))
    else:
        return value


class Technology(pydantic.BaseModel):  # type: ignore
    """
    Represent a technology with region, year, and a flexible set of parameters.

    Attributes
    ----------
    name : str
        Name of the technology.
    region : str
        Region identifier.
    year : int
        Year of the data.
    parameters : Dict[str, Parameter]
        Dictionary of parameter names to Parameter objects.
    case : str
        Case or scenario identifier.
    detailed_technology : str
        More detailed technology name.

    """

    name: typing.Annotated[str, pydantic.Field(description="Name of the technology.")]
    region: typing.Annotated[str, pydantic.Field(description="Region identifier.")]
    year: typing.Annotated[int, pydantic.Field(description="Year of the data.")]
    parameters: typing.Annotated[
        dict[str, Parameter],
        pydantic.Field(default_factory=dict, description="Parameters."),
    ]
    case: typing.Annotated[
        str, pydantic.Field(description="Case or scenario identifier.")
    ]
    detailed_technology: typing.Annotated[
        str, pydantic.Field(description="Detailed technology name.")
    ]

    def __eq__(self, other: object) -> bool:
        """
        Check for equality with another Technology object based on non-None attributes.

        Compares all attributes of the current instance with those of the other object.
        Only compares attributes that are not None in both instances.

        Parameters
        ----------
        other : object
            The object to compare with. Expected to be an instance of Technology.

        Returns
        -------
        bool
            True if all non-None attributes are equal between self and other, False otherwise.
            Returns False if other is not a Technology instance.

        Notes
        -----
        This method considers only attributes that are not None in both objects.
        If an attribute is None in either object, it is ignored in the comparison.

        """
        if not isinstance(other, Technology):
            logger.error("The object is not a Technology instance.")
            return False

        for field in self.__class__.model_fields.keys():
            value_self = getattr(self, field)
            value_other = getattr(other, field)
            if value_self != value_other:
                return False
        return True

    def __hash__(self) -> int:
        """
        Return a hash value for the Technology instance based on all attributes.

        This method computes a combined hash of the instance's attributes to
        uniquely identify the object in hash-based collections such as sets and dictionaries.

        Returns
        -------
        int
            The hash value of the Technology instance.

        """
        # Retrieve all attribute values dynamically
        attribute_values = tuple(
            make_hashable(getattr(self, field))
            for field in self.__class__.model_fields.keys()
        )
        return hash(attribute_values)

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

    def calculate_parameters(
        self, parameters: typing.Any | None = None
    ) -> "Technology":
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

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> "Technology":
        """
        Create an instance of the class from a dictionary.

        Parameters
        ----------
        cls : type
            The class to instantiate.
        data : dict
            A dictionary containing the data to initialize the class instance.
            Expected keys include:
                - "region" (str): The region associated with the instance.
                - "case" (str): The case identifier.
                - "year" (int): The year value.
                - "name" (str): The name of the instance.
                - "detailed_technology" (str): Details about the technology.
                - "parameters" (dict): A dictionary where each key maps to a parameter data
                  dictionary, which will be converted to a Parameter object.

        Returns
        -------
        instance : cls
            An instance of the class initialized with the provided data.

        Notes
        -----
        This method processes the "parameters" field in the input data by converting each
        parameter dictionary into a Parameter object using `Parameter.from_dict()`. It then
        constructs and returns an instance of the class with all the provided attributes.

        """
        params = {}
        for key, param_data in data.get("parameters", {}).items():
            params[key] = Parameter.from_dict(param_data)
        return cls(
            region=data["region"],
            case=data["case"],
            year=data["year"],
            name=data["name"],
            detailed_technology=data["detailed_technology"],
            parameters=params,
        )
