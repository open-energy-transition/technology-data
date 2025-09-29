import pathlib

import pandas

path_cwd = pathlib.Path.cwd()


def get_conversion_dictionary() -> dict:
    """
    Provide conversion dictionaries between data source column names
    and TechnologyCollection attribute names.

    Parameters
    ----------

    Returns
    -------
    Dictionary
        conversion dictionary that renames columns to TechnologyCollection attribute names
    """

    return {
        "Technology": "name",
        "par": "parameters",
        "Variable O&M": "VOM",
        "Fuel": "fuel",
        "Additional OCC": "investment",
            "WACC Real": "discount rate",
    }



if __name__ == "__main__":
    dea_energy_storage_file_path = pathlib.Path(path_cwd, "src", "technologydata", "package_data", "raw", "Technology_datasheet_for_energy_storage.xlsx")
    dea_energy_storage_df = pandas.read_excel(dea_energy_storage_file_path, sheet_name="alldata_flat")

