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
from technologydata.utils.units import (
    CURRENCY_UNIT_PATTERN,
    creg,
    extract_currency_units,
    get_conversion_rate,
    get_iso3_from_currency_code,
    hvreg,
    ureg,
)


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
        # Do not allow for currency conversion here, as it requires additional information
        if extract_currency_units(self._pint_quantity.units) != extract_currency_units(
            units
        ):
            raise NotImplementedError(
                "Currency conversion is not supported in the `to` method. "
                "Use `change_currency` for currency conversions."
            )

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
    def change_currency(
        self, to_currency: str, country: str, source: str = "worldbank"
    ) -> "Parameter":
        """
        Change the currency of the parameter.

        This allows for conversion to a different currency as well as for inflation adjustments.
        To properly adjust for inflation, the function requires the `country` for which the inflation
        adjustment should be applied for.

        Note that this wil harmonise all currencies used in the parameter's units,
        i.e. if the parameter `units` contains multiple different currencies,
        all of them will be converted to the target currency.

        Parameters
        ----------
        to_currency : str
            The target currency unit to convert to, e.g. "USD_2020", "EUR_2024", "CNY_2022".
        country : str
            The country for which the inflation adjustment should be made for.
            Must be the official ISO 3166-1 alpha-3 country code, e.g. "USA", "DEU", "CHN".
        source : str, optional
            The source of the inflation data, either "worldbank" or "imf".
            Defaults to "worldbank".
            Depending on the source, different years to adjust for inflation may be available.

        Returns
        -------
        Parameter
            A new Parameter object with the converted currency.

        Examples
        --------
        >>> param.change_currency("USD_2024", "USA")
        >>> param.change_currency("EUR_2020", "DEU", source="imf")
        >>> param.change_currency("EUR_2023", "USA", source="worldbank")

        """
        # Ensure the target currency is a valid unit
        ureg.ensure_currency_is_unit(to_currency)

        # Current unit and currency/currencies
        from_units = self._pint_quantity.units
        from_currencies = extract_currency_units(from_units)
        # Replace all currency units in the from_units with the target currency
        to_units = CURRENCY_UNIT_PATTERN.sub(to_currency, str(from_units))

        # Create a temporary context to which we add the conversion rates
        # We use a temporary context to avoid polluting the global unit registry
        # with potentially invalid or incomplete conversion rates that do not
        # match the `country` and `source` parameters.
        context = ureg.Context()

        # Conversion rates are all relative to the reference currency
        ref_currency = ureg.get_reference_currency()
        ref_currency_p = CURRENCY_UNIT_PATTERN.match(ref_currency)
        ref_iso3 = get_iso3_from_currency_code(ref_currency_p.group("cu_iso3"))
        ref_year = ref_currency_p.group("year")

        # Get conversion rates for all involved currencies
        currencies = set(from_currencies).union({to_currency})
        # Avoid recursion error in pint definition by re-adding the reference currency
        currencies = currencies - {ref_currency}

        for currency in currencies:
            from_currency = CURRENCY_UNIT_PATTERN.match(currency)
            from_iso3 = get_iso3_from_currency_code(from_currency.group("cu_iso3"))
            from_year = from_currency.group("year")

            conversion_rate = get_conversion_rate(
                from_iso3=from_iso3,
                from_year=from_year,
                to_iso3=ref_iso3,
                to_year=int(ref_year),
                country=country,
                source=source,
            )

            context.redefine(f"{currency} = 1 / {conversion_rate:.4f} * {ref_currency}")

        # Actual conversion using pint
        quantity = self._pint_quantity.to(to_units, context=context)

        return Parameter(
            magnitude=quantity.magnitude,
            units=str(quantity.units),
            carrier=self.carrier,
            heating_value=self.heating_value,
            provenance=self.provenance,
            note=self.note,
            sources=self.sources,
        )

    def _check_parameter_compatibility(self, other: "Parameter") -> None:
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
        self._check_parameter_compatibility(other)
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
        self._check_parameter_compatibility(other)
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
