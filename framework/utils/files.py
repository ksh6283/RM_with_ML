from typing import Union
import os
import pickle
import re
import time
import pandas as pd

# from offlineProfiling.ermsModels import ErmsModel, FittingUsage as UsageModel
from sklearn.tree import DecisionTreeRegressor


def append_data(data: pd.DataFrame, data_path):
    """This method is used to write data to a file, if the file is exist,
    it will append data to the end, otherwise it will create a new file.

    Args:
        data (pd.DataFrame): Data to save
        data_path (str): Path to the file
    """
    if not os.path.exists(data_path):
        open(data_path, "w").close()
    is_empty = os.path.getsize(data_path) == 0
    data.to_csv(data_path, index=False, mode="a", header=is_empty)


RUN_DIR_FORMAT = "%Y%m%d_%H%M%S"
RUN_DIR_PATTERN = re.compile(r"\d{8}_\d{6}")


def dated_data_path(base_path, continues=False):
    """Returns a per-run directory <base_path>/<YYYYMMDD_HHMMSS> so that runs never
    overwrite each other. With continues=True, the latest existing run directory
    is reused (data is appended), falling back to a new one if none exists.
    """
    if continues and os.path.isdir(base_path):
        runs = sorted(x for x in os.listdir(base_path) if RUN_DIR_PATTERN.fullmatch(x))
        if runs:
            return os.path.join(base_path, runs[-1])
    path = os.path.join(base_path, time.strftime(RUN_DIR_FORMAT))
    os.makedirs(path, exist_ok=True)
    return path

def dump_model(model, file_path):
    with open(file_path, "wb") as file:
        pickle.dump(model, file)

# def load_model(file_path) -> Union[ErmsModel, UsageModel, DecisionTreeRegressor]:
#     with open(file_path, "rb") as file:
#         return pickle.load(file)
