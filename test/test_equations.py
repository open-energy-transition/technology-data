# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Tests for Equation, EquationRegistry, and Technology.calculate_parameters."""

import pytest

import technologydata  # noqa: F401 — ensures default_formulas are registered
from technologydata.default_equations import equation_registry
from technologydata.equations import Equation, EquationRegistry
from technologydata.parameter import Parameter
from technologydata.technology import Technology

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

EAC_ANNUITY_PARAMS = {
    "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
    "wacc": Parameter(magnitude=0.07, units="dimensionless"),
    "lifetime": Parameter(magnitude=20.0, units="year"),
}

EAC_SIMPLE_PARAMS = {
    "total_investment_cost": Parameter(magnitude=2000.0, units="USD_2020/kW"),
    "lifetime": Parameter(magnitude=20.0, units="year"),
}

# eac_annuity forward result: 1000 * 0.07 / (1 - 1.07^-20)
_EAC_ANNUITY_EXPECTED = 1000.0 * 0.07 / (1 - 1.07**-20)
# eac_simple forward result: 2000 / 20
_EAC_SIMPLE_EXPECTED = 100.0
# annuity_factor for wacc=0.07, lifetime=20
_AF_EXPECTED = 0.07 / (1 - 1.07**-20)


# ---------------------------------------------------------------------------
# Equation.can_solve_for
# ---------------------------------------------------------------------------


class TestEquationCanSolveFor:
    def test_can_solve_for_target_when_all_others_present(self) -> None:
        link = Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )
        params = {
            "b": Parameter(magnitude=1.0, units="dimensionless"),
            "c": Parameter(magnitude=2.0, units="dimensionless"),
        }
        assert link.can_solve_for("a", params) is True

    def test_cannot_solve_for_target_not_in_parameters(self) -> None:
        link = Equation(
            name="test",
            parameters=["a", "b"],
            eq_str="a - b",
        )
        params = {"a": Parameter(magnitude=1.0, units="dimensionless")}
        assert link.can_solve_for("x", params) is False

    def test_cannot_solve_when_input_missing(self) -> None:
        link = Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )
        # c is missing
        params = {"b": Parameter(magnitude=1.0, units="dimensionless")}
        assert link.can_solve_for("a", params) is False


# ---------------------------------------------------------------------------
# Currency consistency checks
# ---------------------------------------------------------------------------


class TestCurrencyConsistency:
    def _link(self) -> Equation:
        return Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )

    def test_required_matching_currency_years_pass(self) -> None:
        params = {
            "b": Parameter(magnitude=1.0, units="USD_2020/kW"),
            "c": Parameter(magnitude=2.0, units="USD_2020/kW"),
        }
        result = self._link().solve_for("a", params)
        assert result.magnitude == pytest.approx(3.0)
        assert "USD_2020" in (result.units or "")

    def test_no_currency_required_params_does_not_raise(self) -> None:
        params = {
            "b": Parameter(magnitude=0.5, units="year"),
            "c": Parameter(magnitude=0.5, units="year"),
        }
        result = self._link().solve_for("a", params)
        assert result.magnitude == pytest.approx(1.0)

    def test_mixed_with_non_currency_required_param_passes(self) -> None:
        link = Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b * c",
        )
        params = {
            "b": Parameter(magnitude=1000.0, units="USD_2020/kW"),
            "c": Parameter(magnitude=0.07, units="dimensionless"),
        }
        result = link.solve_for("a", params)
        assert result.magnitude == pytest.approx(70.0)
        assert "USD_2020" in (result.units or "")

    def test_extra_non_required_currency_param_is_ignored(self) -> None:
        params = {
            "b": Parameter(magnitude=2.0, units="USD_2020/kW"),
            # `x` is unrelated to this equation and should not be validated.
            "x": Parameter(magnitude=1.0, units="EUR_2020/kW"),
        }
        result = Equation(
            name="test",
            parameters=["a", "b"],
            eq_str="a - b",
        ).solve_for("a", params)
        assert result.magnitude == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# EAC — forward and backward
# ---------------------------------------------------------------------------


class TestEacAnnuity:
    def test_forward_eac(self) -> None:
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.magnitude == pytest.approx(_EAC_ANNUITY_EXPECTED, rel=1e-6)

    def test_forward_eac_currency_inherited(self) -> None:
        # lifetime appears only as exponent, so pint gives USD_2020/kW (not /year)
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert "USD_2020" in result.units
        assert "kilowatt" in result.units  # pint canonicalises kW → kilowatt

    def test_forward_eac_provenance(self) -> None:
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.provenance == "eac_annuity"

    def test_backward_specific_investment(self) -> None:
        eac = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        params = {
            "eac": eac,
            "wacc": EAC_ANNUITY_PARAMS["wacc"],
            "lifetime": EAC_ANNUITY_PARAMS["lifetime"],
        }
        result = equation_registry.calculate("specific_investment", params)
        assert result.magnitude == pytest.approx(1000.0, rel=1e-4)
        assert "USD_2020" in result.units
        assert "kilowatt" in result.units

    def test_backward_lifetime(self) -> None:
        # Solving for lifetime requires log(); pint falls back to magnitudes.
        eac = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        params = {
            "eac": eac,
            "specific_investment": EAC_ANNUITY_PARAMS["specific_investment"],
            "wacc": EAC_ANNUITY_PARAMS["wacc"],
        }
        result = equation_registry.calculate("lifetime", params)
        assert result.magnitude == pytest.approx(20.0, rel=1e-4)


class TestEacSimple:
    def test_forward_eac(self) -> None:
        result = equation_registry.calculate(
            "eac", EAC_SIMPLE_PARAMS, equation_name="eac_simple"
        )
        assert result.magnitude == pytest.approx(_EAC_SIMPLE_EXPECTED)
        assert result.provenance == "eac_simple"
        # eac_simple divides by lifetime directly, so pint gives /year correctly
        assert "kilowatt" in result.units
        assert "year" in result.units

    def test_backward_total_investment_cost(self) -> None:
        eac = equation_registry.calculate(
            "eac", EAC_SIMPLE_PARAMS, equation_name="eac_simple"
        )
        params = {"eac": eac, "lifetime": EAC_SIMPLE_PARAMS["lifetime"]}
        result = equation_registry.calculate(
            "total_investment_cost", params, equation_name="eac_simple"
        )
        assert result.magnitude == pytest.approx(2000.0)


# ---------------------------------------------------------------------------
# Annuity factor
# ---------------------------------------------------------------------------


class TestAnnuityFactor:
    _PARAMS = {
        "wacc": Parameter(magnitude=0.07, units="dimensionless"),
        "lifetime": Parameter(magnitude=20.0, units="year"),
    }

    def test_forward_annuity_factor(self) -> None:
        result = equation_registry.calculate("annuity_factor", self._PARAMS)
        assert result.magnitude == pytest.approx(_AF_EXPECTED, rel=1e-6)
        assert result.units == "dimensionless"
        assert result.provenance == "annuity_factor"

    def test_backward_lifetime(self) -> None:
        # Solving for lifetime requires log(); pint falls back to magnitudes.
        af = equation_registry.calculate("annuity_factor", self._PARAMS)
        params = {
            "annuity_factor": af,
            "wacc": self._PARAMS["wacc"],
        }
        result = equation_registry.calculate("lifetime", params)
        assert result.magnitude == pytest.approx(20.0, rel=1e-4)

    def test_backward_wacc_no_analytical_solution(self) -> None:
        # WACC appears in a transcendental position (both linearly and as an
        # exponent base), so SymPy cannot find a closed-form solution and does not support
        # this type of equation
        af = equation_registry.calculate("annuity_factor", self._PARAMS)
        params = {
            "annuity_factor": af,
            "lifetime": self._PARAMS["lifetime"],
        }
        with pytest.raises(NotImplementedError):
            equation_registry.calculate("wacc", params, equation_name="annuity_factor")

    def test_eac_via_annuity_factor_matches_direct_formula(self) -> None:
        af = equation_registry.calculate("annuity_factor", self._PARAMS)
        params = {
            "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
            "annuity_factor": af,
        }
        eac_via_af = equation_registry.calculate(
            "eac", params, equation_name="eac_via_annuity_factor"
        )
        assert eac_via_af.magnitude == pytest.approx(_EAC_ANNUITY_EXPECTED, rel=1e-6)


# ---------------------------------------------------------------------------
# Total investment cost
# ---------------------------------------------------------------------------


class TestTotalInvestment:
    _SIC = Parameter(magnitude=800.0, units="USD_2020/kW")
    _CAP = Parameter(magnitude=100.0, units="kW")
    _TOTAL_EXPECTED = 80_000.0

    def test_forward_total(self) -> None:
        params = {"specific_investment": self._SIC, "capacity": self._CAP}
        result = equation_registry.calculate("total_investment_cost", params)
        assert result.magnitude == pytest.approx(self._TOTAL_EXPECTED)
        # sic [USD/kW] * capacity [kW] → pint cancels kW, gives currency only
        assert result.units == "USD_2020"

    def test_backward_specific_investment(self) -> None:
        params = {
            "total_investment_cost": Parameter(
                magnitude=self._TOTAL_EXPECTED, units="USD_2020"
            ),
            "capacity": self._CAP,
        }
        result = equation_registry.calculate("specific_investment", params)
        assert result.magnitude == pytest.approx(800.0)
        assert "USD_2020" in result.units

    def test_backward_capacity(self) -> None:
        params = {
            "total_investment_cost": Parameter(
                magnitude=self._TOTAL_EXPECTED, units="USD_2020"
            ),
            "specific_investment": self._SIC,
        }
        result = equation_registry.calculate("capacity", params)
        assert result.magnitude == pytest.approx(100.0)
        assert "kilowatt" in result.units


# ---------------------------------------------------------------------------
# Fixed O&M cost
# ---------------------------------------------------------------------------


class TestFixedOm:
    _SIC = Parameter(magnitude=1000.0, units="USD_2020/kW")
    _FRACTION = Parameter(magnitude=0.03, units="dimensionless")
    _FOM_EXPECTED = 30.0

    def test_forward_fixed_om(self) -> None:
        params = {
            "specific_investment": self._SIC,
            "fixed_om_fraction": self._FRACTION,
        }
        result = equation_registry.calculate("fixed_om", params)
        assert result.magnitude == pytest.approx(self._FOM_EXPECTED)
        assert "USD_2020" in result.units

    def test_backward_fraction(self) -> None:
        params = {
            "fixed_om": Parameter(
                magnitude=self._FOM_EXPECTED, units="USD_2020/kW/year"
            ),
            "specific_investment": self._SIC,
        }
        result = equation_registry.calculate("fixed_om_fraction", params)
        assert result.magnitude == pytest.approx(0.03)

    def test_backward_specific_investment(self) -> None:
        params = {
            "fixed_om": Parameter(
                magnitude=self._FOM_EXPECTED, units="USD_2020/kW/year"
            ),
            "fixed_om_fraction": self._FRACTION,
        }
        result = equation_registry.calculate("specific_investment", params)
        assert result.magnitude == pytest.approx(1000.0)


# ---------------------------------------------------------------------------
# Round-trip efficiency
# ---------------------------------------------------------------------------


class TestRoundtripEfficiency:
    _CE = Parameter(magnitude=0.95, units="dimensionless")
    _DE = Parameter(magnitude=0.90, units="dimensionless")
    _RT_EXPECTED = 0.855

    def test_forward_roundtrip(self) -> None:
        params = {"charge_efficiency": self._CE, "discharge_efficiency": self._DE}
        result = equation_registry.calculate("roundtrip_efficiency", params)
        assert result.magnitude == pytest.approx(self._RT_EXPECTED)
        assert result.units == "dimensionless"

    def test_backward_charge_efficiency(self) -> None:
        params = {
            "roundtrip_efficiency": Parameter(
                magnitude=self._RT_EXPECTED, units="dimensionless"
            ),
            "discharge_efficiency": self._DE,
        }
        result = equation_registry.calculate("charge_efficiency", params)
        assert result.magnitude == pytest.approx(0.95, rel=1e-4)

    def test_backward_discharge_efficiency(self) -> None:
        params = {
            "roundtrip_efficiency": Parameter(
                magnitude=self._RT_EXPECTED, units="dimensionless"
            ),
            "charge_efficiency": self._CE,
        }
        result = equation_registry.calculate("discharge_efficiency", params)
        assert result.magnitude == pytest.approx(0.90, rel=1e-4)


# ---------------------------------------------------------------------------
# Fuel variable cost
# ---------------------------------------------------------------------------


class TestFuelVariableCost:
    _FUEL_COST = Parameter(magnitude=50.0, units="USD_2020/MWh")
    _EFF = Parameter(magnitude=0.5, units="dimensionless")
    _FVC_EXPECTED = 100.0

    def test_forward_fuel_variable_cost(self) -> None:
        params = {"fuel_cost": self._FUEL_COST, "efficiency": self._EFF}
        result = equation_registry.calculate("fuel_variable_cost", params)
        assert result.magnitude == pytest.approx(self._FVC_EXPECTED)
        assert "USD_2020" in result.units

    def test_backward_efficiency(self) -> None:
        params = {
            "fuel_variable_cost": Parameter(
                magnitude=self._FVC_EXPECTED, units="USD_2020/MWh"
            ),
            "fuel_cost": self._FUEL_COST,
        }
        result = equation_registry.calculate("efficiency", params)
        assert result.magnitude == pytest.approx(0.5)
        assert result.units == "dimensionless"

    def test_backward_fuel_cost(self) -> None:
        params = {
            "fuel_variable_cost": Parameter(
                magnitude=self._FVC_EXPECTED, units="USD_2020/MWh"
            ),
            "efficiency": self._EFF,
        }
        result = equation_registry.calculate("fuel_cost", params)
        assert result.magnitude == pytest.approx(50.0)
        assert "USD_2020" in result.units


# ---------------------------------------------------------------------------
# CO₂ cost
# ---------------------------------------------------------------------------


class TestCo2Cost:
    _CO2_PRICE = Parameter(magnitude=80.0, units="USD_2020/t")
    _CO2_INTENSITY = Parameter(magnitude=0.3, units="t/MWh")
    _CO2_COST_EXPECTED = 24.0

    def test_forward_co2_cost(self) -> None:
        params = {"co2_price": self._CO2_PRICE, "co2_intensity": self._CO2_INTENSITY}
        result = equation_registry.calculate("co2_cost", params)
        assert result.magnitude == pytest.approx(self._CO2_COST_EXPECTED)
        assert "USD_2020" in result.units

    def test_backward_co2_price(self) -> None:
        params = {
            "co2_cost": Parameter(
                magnitude=self._CO2_COST_EXPECTED, units="USD_2020/MWh"
            ),
            "co2_intensity": self._CO2_INTENSITY,
        }
        result = equation_registry.calculate("co2_price", params)
        assert result.magnitude == pytest.approx(80.0)
        assert "USD_2020" in result.units

    def test_backward_co2_intensity(self) -> None:
        params = {
            "co2_cost": Parameter(
                magnitude=self._CO2_COST_EXPECTED, units="USD_2020/MWh"
            ),
            "co2_price": self._CO2_PRICE,
        }
        result = equation_registry.calculate("co2_intensity", params)
        assert result.magnitude == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# Formula selection
# ---------------------------------------------------------------------------


class TestFormulaSelection:
    def test_default_formula_chosen_when_not_specified(self) -> None:
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.provenance == "eac_annuity"

    def test_explicit_equation_name_overrides_default(self) -> None:
        result = equation_registry.calculate(
            "eac", EAC_SIMPLE_PARAMS, equation_name="eac_simple"
        )
        assert result.provenance == "eac_simple"

    def test_fallback_to_applicable_when_default_cannot_apply(self) -> None:
        # Only total_investment_cost + lifetime available:
        # eac_annuity is default but requires sic/wacc/lifetime — cannot apply.
        # eac_simple can apply.
        result = equation_registry.calculate("eac", EAC_SIMPLE_PARAMS)
        assert result.provenance == "eac_simple"

    def test_unknown_equation_name_raises(self) -> None:
        with pytest.raises(KeyError, match="No equation named"):
            equation_registry.calculate(
                "eac", EAC_ANNUITY_PARAMS, equation_name="bogus"
            )

    def test_named_formula_with_missing_params_raises(self) -> None:
        with pytest.raises(ValueError, match="missing parameters"):
            equation_registry.calculate(
                "eac",
                {"lifetime": Parameter(magnitude=20.0, units="year")},
                equation_name="eac_annuity",
            )

    def test_no_applicable_formula_raises_with_diagnosis(self) -> None:
        with pytest.raises(ValueError, match="No equation for"):
            equation_registry.calculate(
                "eac",
                {"lifetime": Parameter(magnitude=20.0, units="year")},
            )

    def test_unknown_target_raises(self) -> None:
        with pytest.raises(ValueError, match="No equation registered"):
            equation_registry.calculate("does_not_exist", EAC_ANNUITY_PARAMS)


# ---------------------------------------------------------------------------
# can_calculate
# ---------------------------------------------------------------------------


class TestCanCalculate:
    def test_returns_true_when_applicable(self) -> None:
        assert equation_registry.can_calculate("eac", EAC_ANNUITY_PARAMS) is True

    def test_returns_false_when_inputs_missing(self) -> None:
        assert (
            equation_registry.can_calculate(
                "eac", {"lifetime": Parameter(magnitude=20.0, units="year")}
            )
            is False
        )

    def test_returns_false_for_unknown_target(self) -> None:
        assert (
            equation_registry.can_calculate("unknown_param", EAC_ANNUITY_PARAMS)
            is False
        )


# ---------------------------------------------------------------------------
# Custom registry (isolated from built-in)
# ---------------------------------------------------------------------------


class TestCustomRegistry:
    """Verify users can create an independent registry and register their own formulas."""

    def test_custom_formula_forward(self) -> None:
        reg = EquationRegistry()
        reg.register(
            name="ohms_law",
            parameters=["voltage", "current", "resistance"],
            eq_str="voltage - current * resistance",
        )
        params = {
            "current": Parameter(magnitude=2.0, units="ampere"),
            "resistance": Parameter(magnitude=5.0, units="ohm"),
        }
        result = reg.calculate("voltage", params)
        assert result.magnitude == pytest.approx(10.0)
        # pint returns "ampere * ohm" (correct but not simplified to "volt")
        assert result.units is not None

    def test_custom_formula_backward(self) -> None:
        reg = EquationRegistry()
        reg.register(
            name="ohms_law",
            parameters=["voltage", "current", "resistance"],
            eq_str="voltage - current * resistance",
        )
        params = {
            "voltage": Parameter(magnitude=10.0, units="volt"),
            "resistance": Parameter(magnitude=5.0, units="ohm"),
        }
        result = reg.calculate("current", params)
        assert result.magnitude == pytest.approx(2.0)

    def test_custom_registry_isolated_from_builtin(self) -> None:
        reg = EquationRegistry()
        assert not reg.can_calculate("eac", EAC_ANNUITY_PARAMS)

    def test_parameter_names_with_spaces(self) -> None:
        """Parameter names containing spaces must work end-to-end."""
        reg = EquationRegistry()
        reg.register(
            name="simple_product",
            parameters=["unit cost", "quantity", "total cost"],
            eq_str="total cost - unit cost * quantity",
        )
        params = {
            "unit cost": Parameter(magnitude=800.0, units="USD_2020/kW"),
            "quantity": Parameter(magnitude=100.0, units="kW"),
        }
        result = reg.calculate("total cost", params)
        assert result.magnitude == pytest.approx(80_000.0)
        # pint: USD_2020/kW * kW = USD_2020
        assert result.units == "USD_2020"

        # Backward direction: derive quantity from total cost and unit cost
        params_back = {
            "unit cost": Parameter(magnitude=800.0, units="USD_2020/kW"),
            "total cost": Parameter(magnitude=80_000.0, units="USD_2020"),
        }
        qty = reg.calculate("quantity", params_back)
        assert qty.magnitude == pytest.approx(100.0)
        assert "kilowatt" in qty.units


# ---------------------------------------------------------------------------
# list_equations
# ---------------------------------------------------------------------------


class TestListEquations:
    def test_list_equations_empty_registry(self) -> None:
        reg = EquationRegistry()
        assert reg.list_equations() == []

    def test_list_equations_sorted_case_insensitive(self) -> None:
        reg = EquationRegistry()
        reg.register("beta", ["x", "y"], "x - y")
        reg.register("Alpha", ["a", "b"], "a - b", default=True)
        reg.register("gamma", ["g", "h"], "g - h")

        listed = reg.list_equations()

        assert [entry["name"] for entry in listed] == ["Alpha", "beta", "gamma"]
        assert listed[0] == {
            "name": "Alpha",
            "parameters": ["a", "b"],
            "eq_str": "a - b",
            "default": True,
        }

    def test_list_equations_for_target(self) -> None:
        reg = EquationRegistry()
        reg.register("z_from_xy", ["z", "x", "y"], "z - x - y")
        reg.register("z_from_k", ["z", "k"], "z - k", default=True)
        reg.register("other", ["q", "r"], "q - r")

        listed = reg.list_equations(target="z")

        assert [entry["name"] for entry in listed] == ["z_from_k", "z_from_xy"]

    def test_list_equations_unknown_target_raises(self) -> None:
        reg = EquationRegistry()
        reg.register("z_from_xy", ["z", "x", "y"], "z - x - y")

        with pytest.raises(ValueError, match="No equation registered"):
            reg.list_equations(target="missing_target")

    def test_register_duplicate_equation_name_raises(self) -> None:
        reg = EquationRegistry()
        reg.register("dup_name", ["a", "b"], "a - b")

        with pytest.raises(ValueError, match="already registered"):
            reg.register("dup_name", ["x", "y"], "x - y")


# ---------------------------------------------------------------------------
# Technology.calculate_parameters integration
# ---------------------------------------------------------------------------


class TestTechnologyCalculateParameters:
    def _tech(self, **extra: Parameter) -> Technology:
        params = {**EAC_ANNUITY_PARAMS, **extra}
        return Technology(
            name="electrolyzer",
            detailed_technology="PEM",
            case="base",
            region="DEU",
            year=2030,
            parameters=params,
        )

    def test_explicit_target_calculated(self) -> None:
        result = self._tech().calculate_parameters(targets=["eac"])
        assert "eac" in result.parameters
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_ANNUITY_EXPECTED, rel=1e-6
        )

    def test_returns_new_instance_original_unchanged(self) -> None:
        tech = self._tech()
        _ = tech.calculate_parameters(targets=["eac"])
        assert "eac" not in tech.parameters

    def test_auto_discovery_derives_all_possible_params(self) -> None:
        result = self._tech().calculate_parameters()
        assert "eac" in result.parameters

    def test_already_present_params_not_overwritten(self) -> None:
        sentinel = Parameter(magnitude=999.0, units="USD_2020/kW/year")
        result = self._tech(eac=sentinel).calculate_parameters()
        assert result.parameters["eac"].magnitude == pytest.approx(999.0)

    def test_equation_names_dict_selects_formula(self) -> None:
        tech = Technology(
            name="electrolyzer",
            detailed_technology="PEM",
            case="base",
            region="DEU",
            year=2030,
            parameters=EAC_SIMPLE_PARAMS,
        )
        result = tech.calculate_parameters(
            targets=["eac"], equation_names={"eac": "eac_simple"}
        )
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_SIMPLE_EXPECTED, rel=1e-6
        )

    def test_unrelated_currency_mismatch_is_ignored(self) -> None:
        params = {
            "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
            "wacc": Parameter(magnitude=0.07, units="dimensionless"),
            "lifetime": Parameter(magnitude=20.0, units="year"),
            # Different currency year on a parameter that is not required by
            # the selected equation and should therefore be ignored.
            "total_investment_cost": Parameter(magnitude=2000.0, units="USD_2022/kW"),
        }
        tech = Technology(
            name="electrolyzer",
            detailed_technology="PEM",
            case="base",
            region="DEU",
            year=2030,
            parameters=params,
        )
        result = tech.calculate_parameters(
            targets=["eac"], equation_names={"eac": "eac_annuity"}
        )
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_ANNUITY_EXPECTED, rel=1e-6
        )

    def test_chained_calculation(self) -> None:
        """Derive annuity_factor first, then eac — both in a single call."""
        result = self._tech().calculate_parameters()
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_ANNUITY_EXPECTED, rel=1e-4
        )
