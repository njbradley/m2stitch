import itertools
from collections.abc import Callable
from typing import Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from .translation_computation import extract_overlap_subregion
from .translation_computation import ncc
from m2stitch.typing_utils import FloatArray
from m2stitch.typing_utils import NumArray


def find_local_max_integer_constrained(
    func: Callable[[FloatArray], float],
    init_x: FloatArray,
    limits: FloatArray,
    max_iter: int = 100,
) -> Tuple[FloatArray, float]:
    init_x = np.array(init_x)
    limits = np.array(limits)
    dim = init_x.shape[0]
    assert limits.shape[0] == dim
    value = func(init_x)
    x = init_x
    for i in range(max_iter):
        around_x = [x + np.array(dxs) for dxs in itertools.product(*[[-1, 0, 1]] * dim)]
        around_x = [
            x
            for x in around_x
            if np.all(limits[:, 0] <= x) and np.all(x <= limits[:, 1])
        ]
        around_values = np.array(list(map(func, around_x)))

        max_ind = np.argmax(around_values)
        max_x = around_x[max_ind]
        max_value = around_values[max_ind]
        if max_value <= value:
            return x, value
        else:
            x = max_x
            value = max_value
    return x, value


def refine_translations(images: NumArray, grid: pd.DataFrame, r: float) -> pd.DataFrame:
    for direction in ["north", "west"]:
        for i2, g in tqdm(grid.iterrows(), total=len(grid)):
            i1 = g[direction]
            if pd.isna(i1):
                continue
            image1 = images[i1]
            image2 = images[i2]

            def overlap_ncc(params):
                x, y = params
                subI1 = extract_overlap_subregion(image1, x, y)
                subI2 = extract_overlap_subregion(image2, -x, -y)
                return ncc(subI1, subI2)

            init_values = [
                int(g[f"{direction}_x_second"]),
                int(g[f"{direction}_y_second"]),
            ]
            limits = [
                [init_values[0] - r, init_values[0] + r],
                [init_values[1] - r, init_values[1] + r],
            ]
            values, ncc_value = find_local_max_integer_constrained(
                overlap_ncc, np.array(init_values), np.array(limits)
            )
            grid.loc[i2, f"{direction}_x"] = values[0]
            grid.loc[i2, f"{direction}_y"] = values[1]
            grid.loc[i2, f"{direction}_ncc"] = ncc_value
    for direction in ["north", "west"]:
        for xy in ["x", "y"]:
            key = f"{direction}_{xy}"
            grid[key] = grid[key].astype(pd.Int32Dtype())
    return grid
