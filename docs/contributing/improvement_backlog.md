# Improvement backlog

This document collects bugs, API additions, behavior changes, and code cleanups that were
identified during reviews and while writing the documentation, many of them with the help of
AI agents, but that are deliberately **not** implemented yet.
Each entry names the owning class, a rough signature or the observed behavior, and the
rationale, so it can be picked up as an independent piece of work later.

## 1. Promised in docs/design but missing (highest priority)

These are used or promised in the documentation today, so users following the docs hit errors.

### Public equation removal and lookup on `EquationRegistry`

```python
def unregister(self, name: str) -> None: ...   # KeyError on unknown name
def get(self, name: str) -> Equation: ...      # KeyError on unknown name
```

`docs/user_guide/technology.md` promises users can "remove or add equations", but removal and
single-equation lookup currently require the private `_remove_equation` /
`_equations_by_name`.

## 2. Custom registry plumbing

- `Technology.calculate_parameters` (and the `TechnologyCollection` mirror) should accept
  `equations: EquationRegistry | None = None` like `check_consistency` already does; today the
  default registry is hard-imported, so custom registries (documented in
  `docs/user_guide/equations.md`) cannot drive derivation.
- `EquationRegistry.__contains__(name)`, `__len__()`, `__iter__()` and
  `equations_for(parameter: str) -> list[Equation]`. Besides user convenience, this would let
  `Technology.check_consistency` / `calculate_parameters` stop reaching into the private
  `_equations_by_parameter` index.

## 3. `Parameter` conveniences

- `__rmul__` (and `__neg__`): `2 * param` currently raises `TypeError` while `param * 2` works;
  scalar multiplication should be symmetric. (`__radd__` is only sensible for
  Parameter + Parameter, which already works — skip it.)
- Ordering comparisons `__lt__` / `__le__` / `__gt__` / `__ge__` via pint quantity comparison
  after unit harmonization, mirroring the compatibility checks in `isclose` (useful for
  screening, e.g. `tech["lifetime"] > threshold`).
- `add_provenance(entry: str) -> Self`: clean, supported way to append one history entry now
  that `provenance` is a `list[str]`.

## 4. Collection and technology conveniences

- `Technology.__delitem__` would complete the mapping protocol (the documented way to drop a
  parameter is `del tech.parameters[name]`).

## 5. Deferred code simplifications (behavior-preserving)

Cleanups identified in review but scoped out of the equations-focused simplification pass:

- `Parameter`: a private `_replace(**overrides)` helper — six methods (`to`, `to_currency`,
  `change_heating_value`, the scalar branches of `__truediv__`/`__mul__`, `__pow__`) rebuild
  `Parameter(...)` passing the same seven fields. Must go through the real constructor, not
  `model_copy`, to keep the pint canonicalization in `__init__`.
- `Parameter.__add__`/`__sub__` are identical except for the operator, and all four arithmetic
  operators repeat the provenance/note/sources merge block — factor into `_additive_op` and
  `_merged_metadata` helpers.
- `Parameter.change_heating_value`: remove the `hv_ratios = hv_ratios` no-op branch and the
  unreachable `NotImplementedError` (the first loop always fills `hv_ratios` for every carrier
  dimension), merge the two loops over `dimensionality`, and collapse the `hv_units`
  derivation. Separately worth deciding: an `else: raise` for a target heating value compatible
  with neither LHV nor HHV (currently silently behaves like HHV) — that is a behavior change.
- `TechnologyCollection.get()`: replace the five copy-pasted regex filter blocks with one loop
  over a `{field: pattern}` dict using `getattr` + `str()`.
- `TechnologyCollection.to_currency()`: drop the unused `enumerate` index; use a list
  comprehension like the adjacent `calculate_parameters`.
- `TechnologyCollection.project()`: bind `self.technologies[0]` once (used six times), and fix
  the `'closest'` `NotImplementedError` message that is missing its `f` prefix (the `{param}`
  placeholder is never interpolated).
- `Technology.to_currency()`: replace deep-copy-then-mutate with a dict comprehension +
  `model_copy(update=...)` like `calculate_parameters`, and `country = overwrite_country or
  self.region`.

## 6. Issues found while writing the tutorials

Found while writing the Overview and the Tutorial; each was worked around in the docs.

### Heating values block multiplication with carriers that have none

`Parameter.__mul__` and `__truediv__` require both operands to have the same heating value.
Electricity has none, so the most natural electrolyser calculation fails:

```python
electricity = Parameter(magnitude=10, units="MW", carrier="el")
efficiency = Parameter(magnitude=0.65, units="MWh/MWh", carrier="H2/el", heating_value="LHV")
electricity * efficiency  # ValueError: different heating values: None and lower_heating_value
```

Proposal: treat a missing heating value as compatible and let the result take the one that is
set. The rule for two set heating values also needs a decision: multiplying LHV by LHV
currently yields `lower_heating_value ** 2`. This is a design decision and a behavior change.

### Wrong units for `eac`

`calculate_parameters("eac")` from `specific_investment`, `wacc` and `lifetime` returns
`EUR_2020 / kilowatt` instead of `EUR_2020 / kilowatt / year`. Parameters in exponent positions
are passed as plain magnitudes (see `_get_exponent_symbols` in `equations.py`), so the `year`
of `lifetime` is lost. The unit of the result has to be restored, e.g. by dividing by the unit
of the exponent parameter where the formula implies it, or by declaring the target unit per
equation.

### Derived units are not simplified

A derived `total_investment_cost` from `EUR_2020/kW` and `MW` is reported as
`EUR_2020 * megawatt / kilowatt`. Results of equations (and possibly of `__mul__` /
`__truediv__`) should be passed through pint's `to_reduced_units()`.

### Misleading error message for incompatible units

`Parameter._check_parameter_compatibility` compares currencies before dimensions, so any
mismatch where one side has a currency is reported as
`different currencies or currency years: 'megawatt_hour' and 'EUR_2020 / kilowatt'`.
Check dimensionality first, and only report a currency mismatch when both sides have
compatible dimensions.

### Parameter names differ between datasets and equations

The equations identify parameters by name (`specific_investment`, `total_investment_cost`),
while the parsers keep the source's names (`specific investment` in `dea_energy_storage`,
`investment` in `manual_input_usa`). Equations can therefore not be applied to the bundled
datasets. Options: harmonise parameter keys in the parsers to the equation names (and document
it under "Naming conventions" in the fact sheets), or add an alias mapping to the registry.

### `TechnologyCollection.to_dataframe()` is not a flat table

All parameters end up in one nested `parameters` column. A long format with one row per
technology and parameter (`magnitude`, `units`, `carrier`, `heating_value`) would make the
output usable for filtering and export.

### `DataPackage.to_json()` docstring promises a schema that is not written

The docstring says both files are exported "together with the corresponding data schema", but
`TechnologyCollection.to_json` is called with `output_schema=False`. Either pass
`output_schema=True` or add a parameter and fix the docstring.

### `DataAccessor.download()` writes into the installed package by default

Since `data_path` defaults to the package's `parsers` directory (so that `load()` works from any
working directory), `download()` writes there too. In a non-editable install this is inside
`site-packages` and may not be writable. Related to #92, #95 and #113.

## Considered and rejected

- `Parameter.__hash__`: the class is mutable (pint attributes, provenance list), so hashing
  would be unsafe. Defining `__eq__` without `__hash__` (unhashable) is the correct state.
- `TechnologyCollection.from_csv`: `to_csv` serializes nested structures as strings, so a
  faithful round-trip needs real design work; `from_json` covers loading.
- A logging flag on `check_consistency` (design.md's "warnings are logged" alternate flow): the
  returned status dict already carries the information; callers can log it as they see fit.
