# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT
# TODO implement (Johannes)
"""
UnitValue class for representing a value with an associated unit.

This class is designed to support flexible units, including energy carriers, currencies with years, and more.

Examples
--------
>>> uv = UnitValue(value=100, unit="EUR_2020")
>>> uv.value
100
>>> uv.unit
"EUR_2020"

"""

import logging
import typing

import pint
import pydantic

ureg = pint.UnitRegistry()

logger = logging.getLogger(__name__)


class UnitValue(pydantic.BaseModel):  # type: ignore
    """
    Represent a numerical value with an associated unit of measurement.

    Attributes
    ----------
    value : float
        The numerical value.
    unit : str
        The unit of measurement.

    """

    value: typing.Annotated[float, pydantic.Field(description="The numerical value.")]
    unit: typing.Annotated[str, pydantic.Field(description="The unit of measurement.")]

    def __eq__(self, other: object) -> bool:
        """
        Check for equality with another UnitValue object based on non-None attributes.

        Compares all attributes of the current instance with those of the other object.
        Only compares attributes that are not None in both instances.

        Parameters
        ----------
        other : object
            The object to compare with. Expected to be an instance of UnitValue.

        Returns
        -------
        bool
            True if all non-None attributes are equal between self and other, False otherwise.
            Returns False if other is not a UnitValue instance.

        Notes
        -----
        This method considers only attributes that are not None in both objects.
        If an attribute is None in either object, it is ignored in the comparison.

        """
        if not isinstance(other, UnitValue):
            logger.error("The object is not a UnitValue instance.")
            return False

        for field in self.__class__.model_fields.keys():
            value_self = getattr(self, field)
            value_other = getattr(other, field)
            if value_self != value_other:
                return False
        return True

    def __hash__(self) -> int:
        """
        Return a hash value for the UnitValue instance based on all attributes.

        This method computes a combined hash of the instance's attributes to
        uniquely identify the object in hash-based collections such as sets and dictionaries.

        Returns
        -------
        int
            The hash value of the UnitValue instance.

        """
        # Retrieve all attribute values dynamically
        attribute_values = tuple(
            getattr(self, field) for field in self.__class__.model_fields.keys()
        )
        return hash(attribute_values)

    def to(self, new_unit: str) -> "UnitValue":
        """
        Convert the value to a new unit using pint.

        Parameters
        ----------
        new_unit : str
            The unit to convert to.

        Returns
        -------
        UnitValue
            A new UnitValue instance with the converted value and unit.

        Raises
        ------
        pint.errors.DimensionalityError
            If the units are not compatible.

        """
        q = self.value * ureg(self.unit)
        q_converted = q.to(new_unit)
        return UnitValue(value=q_converted.magnitude, unit=str(q_converted.units))
