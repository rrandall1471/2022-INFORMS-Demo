import pandas as pd
from . import data as d, model as m
from typing import Tuple, List

data_file = "data/data.xlsx"

tasks = pd.read_excel(data_file, "Tasks", index_col=0)
resources = pd.read_excel(data_file, "Resources", index_col=0)
tasks_for_resource = pd.read_excel(data_file, "Tasks For Resources", index_col=[0, 1])

raw_data = d.RawData(tasks, resources, tasks_for_resource)

(is_valid, errors) = raw_data.validate()

if not is_valid:
    raise Exception(", ".join(errors))

model_data = raw_data.transform_to_model_data()

model = m.DemoModel(model_data)
model.build_and_solve()
