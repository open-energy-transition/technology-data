# Parameter Formula System

Many techno-economic parameters are not independent — they are related by well-known
engineering or financial relationships. For example, the Equivalent Annual Cost (EAC)
of a technology can be computed from its specific investment cost, discount rate (WACC),
and economic lifetime. Conversely, if the EAC is known and the lifetime is not, the
same relationship can be used to recover the lifetime.

The formula system lets you register these relationships once and then use them in
**any direction**: whichever parameter is missing is derived automatically from the
others. No re-implementation is needed per direction — a single registration covers all
of them.

## Example

The Equivalent Annual Costs of a technology is the cost of owning and operating the technology over its lifetime, expressed on an annual basis.
It is linked to the specific investment cost, WACC, and lifetime of the technology via the annuity factor:

$$
\text{EAC} = \text{specific investment} \cdot \frac{\text{WACC}}{1 - (1 + \text{WACC})^{-\text{lifetime}}}
$$

Given a technology with the three parameters known, we can use the formula system to calculate the EAC for us:

```python
import technologydata as td

# Three parameters are known
tech = td.Technology(
    name="Electrolysis",
    detailed_technology="PEM",
    case="base",
    region="DEU",
    year=2030,
    parameters={
        "specific_investment": td.Parameter(magnitude=1000.0, units="USD_2020/kW"),
        "wacc":                td.Parameter(magnitude=0.07,   units="dimensionless"),
        "lifetime":            td.Parameter(magnitude=20.0,   units="year"),
    }
)

# Calculate EAC from the three inputs (forward direction)
tech = tech.calculate_parameters("eac")
print(tech.parameters["eac"]) # ≈ 94.4 USD_2020/kilowatt/year
```

This also works in reverse:
If we know the EAC, specific investment, and WACC, we can calculate the lifetime:

```python
tech = td.Technology(
    name="Electrolysis",
    detailed_technology="PEM",
    case="base",
    region="DEU",
    year=2030,
    parameters={
        "specific_investment": td.Parameter(magnitude=1000.0, units="USD_2020/kW"),
        "wacc":                td.Parameter(magnitude=0.07,   units="dimensionless"),
        "eac":                 td.Parameter(magnitude=94.4,   units="USD_2020/kW/year"),
    }
)
# Derive lifetime from EAC instead (reverse direction — same formula)
tech = tech.calculate_parameters("lifetime")
print(tech.parameters["lifetime"])  # ≈ 20.0 years
```

---

## Basic Usage

### Deriving a single parameter

The functionality is not strictly tied to `Technology` objects.
The formula system is tied to `Parameter` objects, of which you can pass one or multiple for calculation to the function `equation_registry.calculate`:

```python
params = {
    "specific_investment": td.Parameter(magnitude=1000.0, units="USD_2020/kW"),
    "wacc":                td.Parameter(magnitude=0.07,   units="dimensionless"),
    "lifetime":            td.Parameter(magnitude=20.0,   units="year"),
}
eac = td.equation_registry.calculate("eac", params)
```

The result of the calculation is a new `Parameter` object with `magnitude`, `units`, and a `provenance` entry
describing the calculation: that the value was derived from other parameters, the name and expression of the
formula used, and the concrete input values it was solved with.

```python
print(eac.provenance[0])
# Calculated from other parameters using formula 'eac_annuity': eac - specific_investment * wacc / (1 - (1 + wacc)**(-lifetime)) = 0
# Input values:
#   specific_investment = 1000.0 USD_2020 / kilowatt
#   wacc = 0.07 dimensionless
#   lifetime = 20.0 year
```

### Checking whether a parameter can be derived

The system automatically checks whether sufficient inputs are present to calculate the requested parameter and raises a `ValueError` if not.
You can manually check whether a parameter can be derived with `equation_registry.can_calculate`:

```python
td.equation_registry.can_calculate("eac", params)   # True - all inputs present
td.equation_registry.can_calculate("wacc", params)  # False - WACC is transcendental
```

### Listing registered equations

You can inspect equations in a registry via `list_equations()`.
The result is a serializable list of dictionaries sorted alphabetically by
equation name (case-insensitive):

```python
all_equations = td.equation_registry.list_equations()
print(all_equations[0])
# {'name': 'annuity_factor',
#  'parameters': ['annuity_factor', 'wacc', 'lifetime'],
#  'eq_str': 'annuity_factor - wacc / (1 - (1 + wacc)**(-lifetime))',
#  'priority': 1,
#  'description': 'Capital recovery factor used to annualize upfront investment.'}

eac_equations = td.equation_registry.list_equations(target="eac")
```

If a target has no registered equations, `list_equations(target=...)` raises
a `ValueError`.

### Displaying equations

`Equation` objects provide a compact REPL representation via `repr(...)`.
The representation includes equation name, parameters (in original order),
equation string, priority, and description.

Long equation strings are truncated for readability in interactive sessions.

```python
eq = td.Equation(
    name="my_equation",
    parameters=["a", "b", "c"],
    eq_str="a - b - c",
)
print(repr(eq))
# Equation(name='my_equation', parameters=['a', 'b', 'c'], eq_str='a - b - c', priority=0, description=None)
```

For a human-readable, math-like rendering use `str(...)` / `print(...)`.
It shows the equation name, the full (untruncated) expression set equal to
zero, and the description if one is set:

```python
eq = td.Equation(
    name="my_equation",
    parameters=["a", "b", "c"],
    eq_str="a - b - c",
    description="a is the sum of b and c.",
)
print(eq)
# my_equation: a - b - c = 0 (a is the sum of b and c.)
```

### Equation solve caching

Symbolic solutions are precomputed and cached when an equation is registered.
This means repeated calculations for the same equation target do not run the
same symbolic solve step again.

If no symbolic solution exists for a target, that information is also cached.
In that case, each calculation skips symbolic solving for that target and uses
the numeric fallback directly with the provided values.

### Integration with `Technology` objects

[`Technology.calculate_parameters`][technologydata.technology.Technology]
wraps the registry so you can derive parameters directly on a `Technology` object.
It always returns a **new** `Technology` instance; the original is never mutated.

```python
tech = td.Technology(
    name="Electrolysis",
    detailed_technology="PEM",
    case="base",
    region="DEU",
    year=2030,
    parameters={
        "specific_investment": td.Parameter(magnitude=800.0, units="USD_2020/kW"),
        "wacc":                td.Parameter(magnitude=0.06,  units="dimensionless"),
        "lifetime":            td.Parameter(magnitude=25.0,  units="year"),
    },
)

# Derive a single parameter
tech_with_eac = tech.calculate_parameters("eac")

# Derive a multiple parameters at once
tech_with_eac = tech.calculate_parameters(["eac", "annuity_factor"])

# Derive everything that can be derived automatically
tech_full = tech.calculate_parameters()
```

Parameters that already present in the technology object are not overwritten by the calculation, even if they are inconsistent with the derived value.
If you want to force a recalculation of an existing parameter, remove it from the `parameters` dictionary first:

```python
tech.parameters.pop("eac")
tech = tech.calculate_parameters("eac")  # now recalculated
```

Derived parameters from intermediate steps are immediately available to subsequent
calculations within the same call, e.g. the automatic calculation above calculates the `annuity_factor` and adds it to the object and then the calculation of the `eac` uses it via the `eac_via_annuity_factor` formula.

---

## Advanced Usage

### Automatic selection of formulas

Sometimes you may have multiple formulas available that can calculate the same parameter.
The registry chooses in this order:

1. An explicitly requested formula via `equation_name=`.
2. The applicable formula with the highest `priority` value.
3. If multiple formulas have the same priority, the first registered one.

If multiple formulas have equal priority for a target, the one that was
registered first and is applicable wins.

If no formula can apply, a `ValueError` is raised that lists every registered formula
and which of its inputs are missing.

### Selecting a specific formula

You can specify a specific formula to use with `equation_name=`:

```python
# Use the default formula (i.e. eac_annuity)
eac = td.equation_registry.calculate("eac", params)

# Specify a specific formula to use (e.g. eac_via_annuity_factor)
tech_alt = tech.calculate_parameters(
    targets=["eac"],
    equation_names={"eac": "eac_via_annuity_factor"},
)
```

### Currency handling

The formula system does not support mixed currencies in a single calculation.
Before a calculation a check is performned that every currency-bearing input uses the same currency *and* currency year (e.g. all `USD_2020`, or all `EUR_2022`).

If the currencies are inconsistent, a `ValueError` is raised immediately:

```python
params_bad = {
    "specific_investment": td.Parameter(magnitude=1000.0, units="USD_2020/kW"),
    "wacc":                td.Parameter(magnitude=0.07,   units="dimensionless"),
    "lifetime":            td.Parameter(magnitude=20.0,   units="year"),
    "eac":                 td.Parameter(magnitude=94.4,   units="USD_2022/kW/year"),
}
td.equation_registry.calculate("specific_investment", params_bad)
# ValueError: Currency mismatch in formula 'eac_annuity':
#   'eac' uses USD_2022, 'specific_investment' uses USD_2020.
#   Harmonise all currency parameters to the same currency and year
#   (e.g. call .to_currency('USD_2020', country=...)) before using this formula.
```

To fix this, harmonise currencies first.

The currency for the result is **inherited automatically** from the inputs.
If all inputs use `EUR_2022`, the calculated parameter will also be in `EUR_2022`.

### Registering custom formulas

You can add your own formulas to the system and use for calculations.
There are two options available:

1. Extend the built-in registry `equation_registry` directly, which makes your formula available globally.
2. Create a separate `EquationRegistry` instance, which keeps your formulas isolated from the built-in ones.
   This also allows you to have multiple isolated registries with different formulas in the same program.

```python
import technologydata as td

# Option 1: extend the global built-in registry
td.equation_registry.register(
    name="lcoe_simplified",
    parameters=["lcoe", "eac", "fixed_om", "full_load_hours"],
    expr_str="lcoe - (eac + fixed_om) / full_load_hours",
)

# Option 2: isolated registry
my_reg = td.EquationRegistry()
```

### Loading equations from YAML files

Equation registries can be populated from YAML files with a list of equation
definitions at the root.

Each entry supports:

- `name`: equation name
- `parameters`: list of parameter names
- `eq_str`: equation string (equal to zero)
- `priority` (optional): non-negative integer, default `0`
- `description` (optional): arbitrary free-text metadata

```python
reg = td.EquationRegistry()
reg.load_from_yaml("my_equations.yaml")

# Load multiple files
reg.load_from_yaml(["base.yaml", "extensions.yaml"])

# Replace an existing equation name intentionally
reg.load_from_yaml("override.yaml", overwrite=True)

# Or create a fresh registry from YAML directly
reg2 = td.EquationRegistry.from_yaml(["base.yaml", "extensions.yaml"])
```

By default (`overwrite=False`), loading fails if a file defines an equation
name that already exists with a different definition.

The built-in default equations are now loaded from a YAML file in
`src/technologydata/equations_data/default_equations.yaml`.
That file declares a YAML language server schema for editor tooltip support.

```python
my_reg.register(
    name="my_formula",
    parameters=["x", "y", "z"],
    expr_str="x - y * z",
    priority=1,
)
result = my_reg.calculate("x", {
    "y": td.Parameter(magnitude=3.0, units="dimensionless"),
    "z": td.Parameter(magnitude=4.0, units="dimensionless"),
})
print(result.magnitude) # 12.0
```

---

## Implementation Details

### How it works

A [`Equation`][technologydata.formulas.Equation] stores a **SymPy expression string** set to zero (e.g. `"eac - sic*wacc/(1-(1+wacc)**(-lifetime))"`) along with the list of participant parameter names.
When asked to solve for a target, it:

1. Maps each parameter name to a positional SymPy symbol (`_p0`, `_p1`, ...) so that names with spaces or other non-identifier characters are supported.
2. Applies a **symbolic-first** strategy: solves the expression with abstract symbols and produces a callable via `sympy.lambdify`. The known parameters are then passed as `pint` Quantity objects, so units are propagated automatically through Python's arithmetic operators.
3. Falls back to **numeric substitution** if the symbolic step yields no result — substitutes the known values first, then calls the solver on the simplified expression.

The [`EquationRegistry`][technologydata.formulas.EquationRegistry] indexes each
`Equation` under every parameter it involves.

### Formula selection

When multiple formulas are registered for the same parameter, the registry selects one following this priority:

| Priority | Condition |
|----------|-----------|
| 1 | A specific formula name was requested via `equation_name=` |
| 2 | Highest-priority formula whose inputs are all present |
| 3 | For equal priority, first registered formula whose inputs are all present |

### Units

Units are propagated automatically using the `pint` Quantity objects that each `Parameter` carries.
The lambdified SymPy solution is evaluated with these Quantities as inputs, so the result inherits consistent units without any annotation on the formula itself.

There are two limitations to be aware of:

- **Exponent parameters**: Parameters that appear only in exponent positions (e.g. `lifetime` in `(1+wacc)**(-lifetime)`) are passed as plain magnitudes. Raising a Quantity to a dimensioned power is physically undefined, and in all real-world formulas such a parameter is a dimensionless count. This means formulas where the output dimension (e.g. `/year`) would only come from an exponent-position parameter — such as `eac_annuity` — will not carry that dimension in the result. Use `eac_simple` (which divides by `lifetime` directly) if the `/year` unit on EAC is important.

- **Transcendental functions**: When the SymPy solution contains a transcendental function (e.g. `log`) applied to a Quantity with physical units, evaluation falls back to magnitude-only, and the result will have `units=None`.

### Limitations

**Transcendental equations** — Some variables cannot be isolated algebraically.
For example, WACC appears both linearly and as an exponent base in the annuity
formula, making it transcendental. Attempting to solve for such a variable raises a
`ValueError`. A 5-second timeout (Unix/Linux) prevents SymPy from hanging indefinitely
on these cases. The affected variable is noted in the built-in formulas reference below.

**Multiple real solutions** — When SymPy returns multiple solutions, the system prefers
positive real values (physical parameters are non-negative by convention) and takes the
first one.

---

## Built-in Formulas Reference

### Capital cost

| Formula name | Parameters | Notes |
|---|---|---|
| `annuity_factor` | `annuity_factor`, `wacc`, `lifetime` | WACC not analytically solvable |
| `eac_annuity` *(highest priority for `eac`)* | `eac`, `specific_investment`, `wacc`, `lifetime` | WACC not analytically solvable |
| `eac_via_annuity_factor` | `eac`, `specific_investment`, `annuity_factor` | Requires pre-computed annuity factor |
| `eac_simple` | `eac`, `total_investment_cost`, `lifetime` | Ignores time-value of money |
| `total_investment_from_specific` | `total_investment_cost`, `specific_investment`, `capacity` | Ensure consistent power units |

### Operations & maintenance

| Formula name | Parameters | Notes |
|---|---|---|
| `fixed_om_from_fraction` | `fixed_om`, `specific_investment`, `fixed_om_fraction` | Fraction is dimensionless (e.g. 0.03 for 3 %/year) |

### Efficiency

| Formula name | Parameters | Notes |
|---|---|---|
| `roundtrip_efficiency` | `roundtrip_efficiency`, `charge_efficiency`, `discharge_efficiency` | All solvable in every direction |

### Variable cost

| Formula name | Parameters | Notes |
|---|---|---|
| `fuel_variable_cost` | `fuel_variable_cost`, `fuel_cost`, `efficiency` | Fuel cost and variable cost must be in same energy unit |
| `co2_cost` | `co2_cost`, `co2_price`, `co2_intensity` | `co2_intensity` in t/MWh of output energy |

```text
```
