# Design

`technologydata` is designed for energy system modellers in mind.
It intendeds to serve common use cases encountered during the design, development and execution of energy system model experiments, such as:

* Screening techno-economic inputs for energy systems
* Comparing techno-economics indicators
* Harmonizing inputs
* Modelling of input assumptions for gap filling
* Transformation of assumptions into model-ready input formats

The project was started for PyPSA-Eur and has since then been expanded to serve more models and purposes.
As such it has been leaning towards serving the purposes of PyPSA-Eur and related models.
We hope to expand it to serve the wider energy system modeling community and a such welcome suggestions and contributions.

## Target audience

The users we target are Energy System Modellers and Analysts.
We assume they are all:

* Familiar with the concept of techno-economics on how to describe technical and economic parameters of technologies for energy system models
* Familiar with the methodology of transforming techno-economic parameters for alignment and harmonization

The users differ in their experience in these fields, but are generally aware of the methodological background behind
the transformations that we make available, like inflation adjustments, currency conversions or unit conversions.

* They prefer simplicity and robustness in use over being able to customize the transformations.
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
    * Interacts with the package either through a Jupyter notebook or wants to be able to use csv / Spreadsheet files for inspection and use of the data.

## Use Cases

Below follow central use cases that we want to serve with `technologydata`.

### 🧾 Use Case ID: UC-001  
#### Title: Screen techno-economic inputs for validity and completeness

#### 🧑‍💻 Actor(s)
- **Primary**: Energy System Modeller, Programmer
- **Secondary**: Energy Analyst (if reviewing pre-screened data)

#### 🎯 Goal
Detect and correct inconsistencies or omissions in techno-economic input data, ensuring it adheres to the package's schema and parameter constraints.

#### 📚 Pre-conditions
- Python environment with `technologydata` installed
- Input data provided as:
  - JSON (conforming to data schema)
  - package-provided JSON files (conforming to schema)
  - user-provided e.g. through the `technologydata` class-interface or through a special pandas DataFrame
- Users are familiar with the structure of `Technology`, `Parameter`, and `Source` classes

#### 🚦 Trigger
- Instantiation of one or more `Technology` object with user-provided or pre-compiled data
- Manual invocation of validation or consistency-check method

#### 🧵 Main Flow

1. User gets/loads or defines technology input (via JSON, DataFrame, or the packaged data).
2. `Technology` object is instantiated, triggering automatic validation.
3. Schema checks enforce:
   - Presence of required fields (e.g., name, parameter value, unit, source)
   - Consistency between parameters (e.g., energy unit alignment)
4. User manually runs `.check_consistency()` or similar method to detect conflicting or incomplete parameters.
5. User manually runs `.calculate_parameters()` to derive
    - specific missing parameters based on known rules (e.g., specific investment, EAC), or
    - all missing parameters that can be derived from the existing parameters
6. The User can manually update parameters, either overwriting existing or adding missing ones.
7. Validated and completed `Technology` object is now ready for transformation or analysis.

#### 🔁 Alternate Flows

- **Invalid schema**:
  - System raises a validation exception and rejects the data.
- **Inconsistent parameters**:
  - Warnings are logged; object remains instantiable but marked as incomplete.
- **Partial data**:
  - User is able to complete missing fields to the `Technology` object

#### ✅ Post-conditions
- One or more `Technology` objects validated and completed with all parameters that can be derived, or
- Errors on schema-violations and Warning about inconsistencies are logged.

#### 🧪 Sample Input/Output

```python
from technologydata import DataPackage
dp = DataPackage.from_json("path/to/data_package") # triggers validation
techs = dp.technologies # Access the TechnologyContainer

techs.check_consistency() # Checks all technologies for consistency
techs = techs.calculate_parameters(parameters=["specific-investment", "eac"])

tech = techs[0] # Access a specific Technology object

tech.check_consistency()  # Check consistency of a single Technology object
tech = tech.calculate_parameters(parameters="missing")  # Calculate missing parameters

tech["parameter_name"]  # Access a specific parameter
tech["parameter_name"] = "new_value"  # Update a parameter value
```

#### 📊 Importance & Frequency

* Importance: High
* Usage Frequency: Frequent, core workflow entry point

#### 📌 Notes

* Consistency logic includes checks for units, and dependency constraints between parameters (e.g. one parameter may be derived from one or more other parameters).
* Schema-based validation is extensible to new parameter types and sources.
