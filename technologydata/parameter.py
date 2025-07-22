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

from technologydata.source import Source
from technologydata.source_collection import SourceCollection

ureg = pint.UnitRegistry()
pint.set_application_registry(ureg)


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
    units: Annotated[str | None, Field(description="The unit of the parameter.")]
    carrier: Annotated[
        str | None,
        Field(description="Carriers of the units, e.g. 'H2', 'el', 'H2O'."),
    ]
    heating_value: Annotated[
        str | None,
        Field(description="Heating value type for energy carriers ('LHV' or 'HHV')."),
    ]
    provenance: Annotated[str | None, Field(description="The data's provenance.")]
    note: Annotated[str | None, Field(description="Additional notes.")]
    sources: Annotated[
        SourceCollection | None,
        Field(description="List of sources for this parameter."),
    ]

    # Private attributes for derived pint objects
    _pint_quantity: pint.Quantity = PrivateAttr(None)
    _pint_carrier: pint.Unit = PrivateAttr(None)
    _pint_heating_value: pint.Unit = PrivateAttr(None)

    def __init__(self, **data: object) -> None:
        """Initialize Parameter and update pint attributes."""
        super().__init__(**data)
        self._update_pint_attributes()

    def _update_pint_attributes(self) -> None:
        """Update all derived pint attributes from current fields."""
        # Update pint quantity
        if self.units:
            self._pint_quantity = pint.Quantity(self.magnitude, self.units)
        else:
            self._pint_quantity = pint.Quantity(self.magnitude)
        # Update carrier
        if self.carrier:
            try:
                self._pint_carrier = ureg.Unit(self.carrier)
            except pint.errors.UndefinedUnitError:
                ureg.define(f"{self.carrier} = [carrier]")
                self._pint_carrier = ureg.Unit(self.carrier)
        else:
            self._pint_carrier = None
        # Update heating value
        if self.heating_value:
            try:
                self._pint_heating_value = ureg.Unit(self.heating_value)
            except pint.errors.UndefinedUnitError:
                ureg.define(f"{self.heating_value} = [heating_value]")
                self._pint_heating_value = ureg.Unit(self.heating_value)
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


