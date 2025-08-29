# SPDX-FileCopyrightText: 2025 The technology-data authors
# SPDX-License-Identifier: MIT
"""Unit tests for growth models in technologydata.technologies.growth_models."""

import numpy as np
import pytest

from technologydata.technologies.growth_models import (
    ExponentialGrowth,
    GompertzGrowth,
    LinearGrowth,
    LogisticGrowth,
)


def test_linear_add_data_points():
    m = 2.0
    c = 1.0

    x = np.arange(-10, 30)
    y = m * x + c

    model = LinearGrowth()
    for xi, yi in zip(x, y):
        model.add_data((xi, yi))
    model.fit(p0={"m": m, "c": c})

    assert model.m == pytest.approx(m, rel=1e-2)
    assert model.c == pytest.approx(c, rel=1e-2)


def test_linear_growth_projection():
    m = 2.0
    c = 5.0
    x = 10
    model = LinearGrowth(m=2.0, c=5.0, data_points=[])
    assert model.project(10) == pytest.approx(m * x + c)


def test_linear_growth_fit():
    m = 2.0
    c = 1.0

    x = np.arange(-10, 30)
    y = m * x + c

    model = LinearGrowth(m=None, c=None, data_points=[*zip(x, y)])
    model.fit(p0={"m": m, "c": c})
    assert model.m == pytest.approx(m, rel=1e-2)
    assert model.c == pytest.approx(c, rel=1e-2)


def test_exponential_growth_projection():
    A = 2.0
    k = 0.5
    x0 = 0.0
    x = 2

    model = ExponentialGrowth(A=A, k=k, x0=x0, data_points=[])
    assert model.project(2) == pytest.approx(A * np.exp(k * (x - x0)))


def test_exponential_growth_fit():
    A = 2.0
    k = 0.5
    x0 = 0.0

    x = np.arange(0, 30)
    y = A * np.exp(k * (x - x0))

    model = ExponentialGrowth(A=None, k=None, x0=None, data_points=[*zip(x, y)])
    model.fit(p0={"A": A, "k": k, "x0": x0})

    assert model.A == pytest.approx(A, rel=1e-2)
    assert model.k == pytest.approx(k, rel=1e-2)
    assert model.x0 == pytest.approx(x0, rel=1e-2)


def test_logistic_growth_projection():
    L = 10.0
    k = 1.0
    x0 = 0.0

    model = LogisticGrowth(L=L, k=k, x0=x0, data_points=[])
    assert model.project(0) == pytest.approx(L / (1 + np.exp(-k * (0 - x0))))


def test_logistic_growth_fit():
    L = 10.0
    k = 1.0
    x0 = 0.0

    x = np.arange(-2, 30)
    y = L / (1 + np.exp(-k * (x - x0)))

    model = LogisticGrowth(L=None, k=None, x0=None, data_points=[*zip(x, y)])
    model.fit(p0={"L": L, "k": k, "x0": x0})

    assert model.L == pytest.approx(L, rel=1e-2)
    assert model.k == pytest.approx(k, rel=1e-2)
    assert model.x0 == pytest.approx(x0, rel=1e-2)


def test_gompertz_growth_projection():
    A = 10.0
    k = 1.0
    x0 = 0.0
    b = 1.0

    model = GompertzGrowth(A=A, k=k, x0=x0, b=b, data_points=[])

    assert model.project(0) == pytest.approx(A * np.exp(-b * np.exp(-k * (0 - x0))))


def test_gompertz_growth_fit():
    A = 10.0
    k = 1.0
    x0 = 0.0
    b = 1.0

    x = np.arange(-2, 30)
    y = A * np.exp(-b * np.exp(-k * (x - x0)))

    model = GompertzGrowth(A=None, k=None, x0=None, b=None, data_points=[*zip(x, y)])
    model.fit(p0={"A": A, "k": k, "x0": x0, "b": b})

    assert model.A == pytest.approx(A, rel=1e-2)
    assert model.k == pytest.approx(k, rel=1e-2)
    assert model.x0 == pytest.approx(x0, rel=1e-2)
    assert model.b == pytest.approx(b, rel=1e-2)


# TODO: Add tests for
# - partial fitting (some parameters fixed)
# - fitting with noise/without p0
# - illegal arguments to p0
