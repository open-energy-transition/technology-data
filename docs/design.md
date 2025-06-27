# Design

`technologydata` is designed for energy system modellers in mind.
It intendeds to serve common use cases encountered during the design, development and execution of energy system model experiments, such as:

* Screening techno-economic inputs for energy systems
* Comparing techno-economics indicators
* Haronising inputs
* Modelling of input assumptions for gap filling
* Transformation of assumptions into model-ready input formats

The project was started for PyPSA-Eur and has since then been expanded to serve more models and purposes.
As such it has been leaning towards serving the purposes of PyPSA-Eur and related models.
We hope to expand it to serve the wider energy system modeling community and a such welcome suggestions and contributions.

## Target audience

The users we target are Energy System Modellers and Analysts.
We assume they are all:

* Familiar with the concept of techno-economics on how to describe technical and economic parameters of technologies for energy system models
* Familiar with the methodology of transforming techno-economic parameters for alignment and harmonisation

The users differ in their experience in these fields, but are generally aware of the methodological background behind
the transformations that we make available, like inflation adjustments, currency conversions or unit conversions.

* They prefer simplicity and robustness in use over being able to customise the transformations.
* They would like to be offered a range of options to choose from, but not too many.
* They would like to be able to use the package without having to read too much documentation, but require clear documentation on the transformations that are applied.
* Data provenance and reproducibility are important to them, so they need to be able to trace data back to its source and understand all individual steps that were applied in the transformation process to the data.

The users differ in their experience with Python and programming in general, we aim to serve three main user types:

1. Programmers and Data Engineers:
    * Well familiar with using Python and object-oriented programming languages, data processing and exchange formats.
    * Interacts with the package through Python scripts, Python modules and Jupyter notebooks.
2. Energy System Modeller:
    * Only basic Python programming skills.
    * Interacts with the package through a Jupyter notebook or a Python script; may want to simply access and inspect the data without writing and executing code.
3. Energy Analyst:
    * No programming skills or only very basic Python skills like using pandas or DataFrames.
    * Interacts with the package either through a Jupyer notebook or wants to be able to use csv / Spreadsheet files for inspection and use of the data.