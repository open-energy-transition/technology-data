# API improvement proposals

This document collects API additions, behavior changes, and code cleanups that were identified
during a review of the formula-system branch but deliberately **not** implemented yet.
Each entry names the owning class, a rough signature, and the rationale, so it can be picked up
as an independent piece of work later.

## 1. Promised in docs/design but missing (highest priority)

These are used or promised in the documentation today, so users following the docs hit errors.

### `TechnologyCollection.__getitem__`

```python
def __getitem__(self, index: int | slice) -> Technology | Self: ...
```

`docs/user_guide/design.md` shows `tech = techs[0]` (twice), but indexing a collection currently
raises `TypeError` even though `__iter__` and `__len__` exist. Integer indices should return the
`Technology`, slices a new `TechnologyCollection`.

### Optional filter arguments on `TechnologyCollection.get`

All five arguments (`name`, `region`, `year`, `case`, `detailed_technology`) are currently
required, although the method body already handles `None` and `design.md` shows partial
filtering (`techs.get(technology="Solar PV", region="EUR")`). Give every argument a `= None`
default.

### Public equation removal and lookup on `EquationRegistry`

```python
def unregister(self, name: str) -> None: ...   # KeyError on unknown name
def get(self, name: str) -> Equation: ...      # KeyError on unknown name
```

`docs/user_guide/technology.md` promises users can "remove or add equations", but removal and
single-equation lookup currently require the private `_remove_equation` /
`_equations_by_name`.

### `TechnologyCollection.get_parameter`

```python
def get_parameter(self, name: str) -> list[Parameter | None]: ...
```

`design.md` shows cross-collection parameter access (`techs["lifetime"].values`). A method
returning one entry per technology (with `None` or a skip-policy for technologies lacking the
parameter) covers the use case without overloading `__getitem__` semantics.

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

## 4. Provenance recording in transformations (behavior change)

`to()`, `to_currency()`, and `change_heating_value()` currently copy `provenance` unchanged
(see the `TODO` in `change_heating_value`). They should append a human-readable history entry,
e.g. `"Converted from USD_2020/kW to EUR_2020/kW."`, completing the provenance-history design
introduced with `provenance: list[str]`.

Note this is an observable behavior change: converted parameters gain provenance entries, and
`test/test_parameter.py` asserts `converted.provenance == param.provenance` after
`to_currency`, which would need updating.

## 5. Collection and technology conveniences

- `TechnologyCollection.append(tech)` and `__add__(other) -> Self`: merge primitive for
  combining harmonized datasets (design.md UC-002); currently requires
  `TechnologyCollection(technologies=a.technologies + b.technologies)` by hand.
- `Technology.__contains__(key)`: `"eac" in tech` is natural given `__getitem__`/`__setitem__`
  exist. `__delitem__` would complete the mapping protocol (the documented way to drop a
  parameter is `del tech.parameters[name]`).
- Compact `__str__` for `Technology` and `TechnologyCollection`: the pydantic repr dumps full
  nested parameters, which is unreadable in a REPL. A summary (name/region/year/case + parameter
  names) matches the `__str__` methods recently added to `Parameter` and `Equation`.

## 6. Deferred code simplifications (behavior-preserving)

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

## Considered and rejected

- `Parameter.__hash__`: the class is mutable (pint attributes, provenance list), so hashing
  would be unsafe. Defining `__eq__` without `__hash__` (unhashable) is the correct state.
- `TechnologyCollection.from_csv`: `to_csv` serializes nested structures as strings, so a
  faithful round-trip needs real design work; `from_json` covers loading.
- A logging flag on `check_consistency` (design.md's "warnings are logged" alternate flow): the
  returned status dict already carries the information; callers can log it as they see fit.
