# Release Notes

<!--

## Upcoming Release

!!! warning "Unreleased Features"

    The features listed below are not released yet, but will be part of the next release!
    To use the features already you have to clone and install the repository from GitHub, e.g. using
    ``pip install git+https://github.com/open-energy-transition/technology-data``.
-->

## Release v0.2.2

*Released 2026-02-06.*

- Avoid repeated calls to `change_heating_value` ([#87](https://github.com/open-energy-transition/technology-data/pull/87)).

## Release v0.2.1

*Released 2026-02-02.*

- Documentation: add pre-commit checks.

## Release v0.2.0

*Released 2026-02-02.*

- Add the `manual_input_usa` parser and its bundled dataset
  ([#68](https://github.com/open-energy-transition/technology-data/pull/68)).

## Release v0.1.0

*Released 2026-01-19.*

First version of the new `technologydata` prototype, introducing the package structure, the
unit-ful `Parameter`, the `Technology` and `TechnologyCollection` models, currency and
heating-value conversion, and the `dea_energy_storage` parser.
