# Copyright 2021 The Layout Parser team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import json
from typing import Dict, List, Union

import pandas as pd

from layoutparser.elements import (
    BASECOORD_ELEMENT_NAMEMAP,
    BaseLayoutElement,
    Layout,
    TextBlock,
)


def load_json(filename: str) -> Union[BaseLayoutElement, Layout]:
    """Load a JSON file and save it as a layout object with appropriate data types.

    Args:
        filename (str):
            The name of the JSON file.

    Returns:
        Union[BaseLayoutElement, Layout]:
            Based on the JSON file format, it will automatically parse
            the type of the data and load it accordingly.
    """
    with open(filename) as fp:
        res = json.load(fp)

    return load_dict(res)


def load_dict(data: Union[Dict, List[Dict]]) -> Union[BaseLayoutElement, Layout]:
    """Load a dict of list of dict representations of some layout data,
    automatically parse its type, and save it as any of BaseLayoutElement
    or Layout datatype.

    Args:
        data (Union[Dict, List]):
            A dict of list of dict representations of the layout data

    Raises:
        ValueError:
            If the data format is incompatible with the layout-data-JSON format,
            raise a `ValueError`.
        ValueError:
            If any `block_type` name is not in the available list of layout element
            names defined in `BASECOORD_ELEMENT_NAMEMAP`, raise a `ValueError`.

    Returns:
        Union[BaseLayoutElement, Layout]:
            Based on the dict format, it will automatically parse the type of
            the data and load it accordingly.
    """
    if isinstance(data, dict):
        if "page_data" in data:
            # It is a layout instance
            return Layout(load_dict(data["blocks"])._blocks, page_data=data["page_data"])
        if data["block_type"] not in BASECOORD_ELEMENT_NAMEMAP:
            raise ValueError(f"Invalid block_type {data['block_type']}")

        # Check if it is a textblock
        is_textblock = any(ele in data for ele in TextBlock._features)
        return (
            TextBlock.from_dict(data)
            if is_textblock
            else BASECOORD_ELEMENT_NAMEMAP[data["block_type"]].from_dict(data)
        )

    elif isinstance(data, list):
        return Layout([load_dict(ele) for ele in data])

    else:
        raise ValueError("Invalid input JSON structure.")


def load_csv(filename: str, block_type: str = None) -> Layout:
    """Load the Layout object from the given CSV file.

    Args:
        filename (str):
            The name of the CSV file. A row of the table represents
            an individual layout element.

        block_type (str):
            If there's no block_type column in the CSV file,
            you must pass in a block_type variable such that layout parser
            can appropriately detect the type of the layout elements.

    Returns:
        Layout:
            The parsed Layout object from the CSV file.
    """

    return load_dataframe(pd.read_csv(filename), block_type=block_type)


def load_dataframe(df: pd.DataFrame, block_type: str = None) -> Layout:
    """Load the Layout object from the given dataframe.

    Args:
        df (pd.DataFrame):

        block_type (str):
            If there's no block_type column in the CSV file,
            you must pass in a block_type variable such that layout parser
            can appropriately detect the type of the layout elements.

    Returns:
        Layout:
            The parsed Layout object from the CSV file.
    """
    df = df.copy()
    if "points" in df.columns and df["points"].dtype == object:
        df["points"] = df["points"].map(lambda x: x if pd.isna(x) else ast.literal_eval(x))

    if block_type is None:
        if "block_type" not in df.columns:
            raise ValueError("`block_type` not specified both in dataframe and arguments")
    else:
        df["block_type"] = block_type
    if any(col in TextBlock._features for col in df.columns) and "id" not in df.columns:
        df["id"] = df.index
    return load_dict(df.apply(lambda x: x.dropna().to_dict(), axis=1).to_list())
