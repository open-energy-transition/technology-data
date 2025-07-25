# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
Parameter class for encapsulating a value, its unit, provenance, notes, and sources.

Examples
--------
>>> from technologydata.source import Source
>>> uv = pint.Quantity(1000, "EUR_2020/kW")
>>> src = Source(name="Example Source", authors="some authors", url="http://example.com")
>>> param = Parameter(quantity=uv, provenance="literature", note="Estimated", sources=[src])

"""

from collections.abc import Callable
from functools import wraps
from typing import Annotated, Any

import pint
from pydantic import BaseModel, Field, PrivateAttr

from technologydata.source_collection import SourceCollection
from technologydata.utils.units import creg, hvreg, ureg


def refresh_pint_attributes(method: Callable[..., Any]) -> Callable[..., Any]:
    """
    Return a decorator to refresh the pint attributes before a method's execution.

    Use this with methods from the `Parameter` class that utilise
    the pint attributes to ensure they are up-to-date before they are used.
    """

    @wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        self._update_pint_attributes()
        result = method(self, *args, **kwargs)
        return result

    return wrapper


class Parameter(BaseModel):  # type: ignore
    """
    Encapsulate a value with its unit, provenance, notes, sources, and more optional attributes required to describe technology parameters, like carrier, and heating value.

    Attributes
    ----------
    magnitude : float
        The numerical value of the parameter.
    units : Optional[str]
        The unit of the parameter.
    carrier : Optional[str]
        The energy carrier.
    heating_value : Optional[str]
        The heating value type.
    provenance : Optional[str]
        Description of the data's provenance.
    note : Optional[str]
        Additional notes about the parameter.
    sources : Optional[SourceCollection]
        List of sources for the parameter.

    """

    magnitude: Annotated[
        float, Field(description="The numerical value of the parameter.")
    ]
    units: Annotated[str | None, Field(description="The unit of the parameter.")] = None
    carrier: Annotated[
        str | None,
        Field(description="Carriers of the units, e.g. 'H2', 'el', 'H2O'."),
    ] = None
    heating_value: Annotated[
        str | None,
        Field(description="Heating value type for energy carriers ('LHV' or 'HHV')."),
    ] = None
    provenance: Annotated[str | None, Field(description="The data's provenance.")] = (
        None
    )
    note: Annotated[str | None, Field(description="Additional notes.")] = None
    sources: Annotated[
        SourceCollection,
        Field(description="List of sources for this parameter."),
    ] = SourceCollection(sources=[])

    # Private attributes for derived pint objects
    _pint_quantity: pint.Quantity = PrivateAttr(None)
    _pint_carrier: pint.Unit = PrivateAttr(None)
    _pint_heating_value: pint.Unit = PrivateAttr(None)

    def __init__(self, **data: object) -> None:
        """Initialize Parameter and update pint attributes."""
        # pint uses canonical names for units, carriers, and heating values
        # Ensure the Parameter object is always created with these consistent names from pint
        if "units" in data and data["units"] is not None:
            ureg.ensure_currency_is_unit(data["units"])
            data["units"] = str(ureg.Unit(data["units"]))
        if "carrier" in data and data["carrier"] is not None:
            data["carrier"] = str(creg.Unit(data["carrier"]))
        if "heating_value" in data and data["heating_value"] is not None:
            data["heating_value"] = str(hvreg.Unit(data["heating_value"]))

        super().__init__(**data)
        self._update_pint_attributes()

    def _update_pint_attributes(self) -> None:
        """Update all derived pint attributes from current fields."""
        # Create a pint quantity from magnitude and units
        if self.units:
            # `units` may contain an undefined currency unit - ensure the ureg can handle it
            ureg.ensure_currency_is_unit(self.units)

            self._pint_quantity = ureg.Quantity(self.magnitude, self.units)
        else:
            self._pint_quantity = ureg.Quantity(self.magnitude)
        # Create the carrier as pint unit
        if self.carrier:
            self._pint_carrier = creg.Unit(self.carrier)
        else:
            self._pint_carrier = None

        # Create the heating value as pint unit
        if self.heating_value and self.carrier:
            self._pint_heating_value = hvreg.Unit(self.heating_value)
        elif self.heating_value and not self.carrier:
            raise ValueError(
                "Heating value cannot be set without a carrier. Please provide a valid carrier."
            )
        else:
            self._pint_heating_value = None

    @refresh_pint_attributes
    def to(self, units: str) -> "Parameter":
        """Convert the parameter's quantity to new units."""
        self._pint_quantity = self._pint_quantity.to(units)
        return Parameter(
            magnitude=self._pint_quantity.magnitude,
            units=str(self._pint_quantity.units),
            carrier=self.carrier,
            heating_value=self.heating_value,
            provenance=self.provenance,
            note=self.note,
            sources=self.sources,
        )

    @refresh_pint_attributes
    def convert_currency(
        self, to: str, region: str = "USA", source: str = "worldbank"
    ) -> pint.Quantity:
        """Currency conversion is not implemented yet. This is a stub."""
        raise NotImplementedError(
            "Currency conversion is not implemented yet. This is a stub."
        )

    def _check_parameter_compatability(self, other: "Parameter") -> None:
        """Check if the parameter's units, carrier, and heating value are compatible."""
        if self._pint_carrier != other._pint_carrier:
            raise ValueError(
                f"Cannot convert between parameters with different carriers: "
                f"{self._pint_carrier} and {other._pint_carrier}."
            )
        if self._pint_heating_value != other._pint_heating_value:
            raise ValueError(
                f"Cannot convert between parameters with different heating values: "
                f"{self._pint_heating_value} and {other._pint_heating_value}."
            )

    def __add__(self, other: "Parameter") -> "Parameter":
        """Add two parameters together."""
        self._check_parameter_compatability(other)
        new_quantity = self._pint_quantity + other._pint_quantity
        return Parameter(
            magnitude=new_quantity.magnitude,
            units=new_quantity.units,
            carrier=self.carrier,
            heating_value=self.heating_value,
            # TODO implement
            # provenance=... ,
            # note=... ,
            # sources=...,
        )

    def __sub__(self, other: "Parameter") -> "Parameter":
        """Subtract two parameters."""
        self._check_parameter_compatability(other)
        new_quantity = self._pint_quantity - other._pint_quantity
        return Parameter(
            magnitude=new_quantity.magnitude,
            units=str(new_quantity.units),
            carrier=self.carrier,
            heating_value=self.heating_value,
            # TODO implement
            # provenance= ... ,
            # note= ... ,
            # sources= ...,
        )

    def __truediv__(self, other: "Parameter") -> "Parameter":
        """Divide two parameters."""
        # We don't check general compatibility here, as division is not a common operation for parameters.
        # Only ensure that the heating values are compatible.
        if self._pint_heating_value != other._pint_heating_value:
            raise ValueError(
                f"Cannot divide parameters with different heating values: "
                f"{self._pint_heating_value} and {other._pint_heating_value}."
            )

        new_quantity = self._pint_quantity / other._pint_quantity
        new_carrier = (
            self._pint_carrier / other._pint_carrier
            if self._pint_carrier and other._pint_carrier
            else None
        )
        new_heating_value = self._pint_heating_value / other._pint_heating_value
        return Parameter(
            magnitude=new_quantity.magnitude,
            units=str(new_quantity.units),
            carrier=str(new_carrier),
            heating_value=str(new_heating_value),
            # TODO implement
            # provenance= ... ,
            # note= ... ,
            # sources= ...,
        )

    def __mul__(self, other: "Parameter") -> "Parameter":
        """Multiply two parameters."""
        # We don't check general compatibility here, as multiplication is not a common operation for parameters.
        # Only ensure that the heating values are compatible.
        if self._pint_heating_value != other._pint_heating_value:
            raise ValueError(
                f"Cannot multiply parameters with different heating values: "
                f"{self._pint_heating_value} and {other._pint_heating_value}."
            )

        new_quantity = self._pint_quantity * other._pint_quantity
        new_carrier = (
            self._pint_carrier * other._pint_carrier
            if self._pint_carrier and other._pint_carrier
            else None
        )
        new_heating_value = self._pint_heating_value * other._pint_heating_value
        return Parameter(
            magnitude=new_quantity.magnitude,
            units=str(new_quantity.units),
            carrier=str(new_carrier),
            heating_value=str(new_heating_value),
            # TODO implement
            # provenance= ... ,
            # note= ... ,
            # sources= ...,
        )
