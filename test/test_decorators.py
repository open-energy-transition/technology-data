"""Tests for decorators."""

import pandas as pd
import pytest
from technologydata.decorators import keep_unmodified_rows


# Create a dummy class to test the decorator
class DummyClass:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    @keep_unmodified_rows(id_columns=["id"], value_columns=["value1", "value2"])
    def modify_data(self, new_data: pd.DataFrame, keep_unmodified=True):
        # Simulate modifying the data
        self.data.update(new_data)
        return self.data


@pytest.fixture
def original_data():
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "value1": [10, 20, 30],
            "value2": [100, 200, 300],
        }
    )


@pytest.fixture
def new_data():
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "value1": [10, 25, 30],  # Modified values
            "value2": [100, 250, 300],  # Only second value modified
        }
    )


def test_keep_unmodified_rows_with_keep_unmodified(original_data, new_data):
    dummy_instance = DummyClass(original_data)
    dummy_instance.modify_data(new_data, keep_unmodified=True)

    expected_data = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "value1": [10, 25, 30],
            "value2": [100, 250, 300],
        }
    )

    pd.testing.assert_frame_equal(dummy_instance.data, expected_data)


def test_keep_unmodified_rows_without_keep_unmodified(original_data, new_data):
    dummy_instance = DummyClass(original_data)
    dummy_instance.modify_data(new_data, keep_unmodified=False)

    expected_data = pd.DataFrame(
        {
            "id": [2],
            "value1": [25],
            "value2": [250],
        }
    )

    pd.testing.assert_frame_equal(dummy_instance.data, expected_data)
