from __future__ import annotations
import pandas as pd
import dataclasses as dc
from typing import cast, Dict, List, Any, Union, Tuple
import json


@dc.dataclass
class ModelData:
    tasks: pd.DataFrame
    resources: pd.DataFrame
    tasks_for_resource: pd.DataFrame


@dc.dataclass
class RawData:
    tasks: pd.DataFrame
    resources: pd.DataFrame
    tasks_for_resource: pd.DataFrame

    @classmethod
    def from_json(cls, json_data: Union[str, Dict[str, Any]]) -> RawData:
        """This function will load a json data set into an instance of RawData
         to feed into the model.

        Args:
            json_data (Union[str, Dict[str, Any]]): The json data that will be
             used as raw data in this solve

        Raises:
            Exception: Raises exception if data is missing

        Returns:
            RawData: The raw data object represented by this json data.
        """
        json_dict: Dict[str, Any]

        if isinstance(json_data, str):
            json_dict = json.loads(json_data)
        else:
            json_dict = json_data

        if "tasks" in json_dict:
            tasks = pd.DataFrame.from_dict(
                json_dict["tasks"], orient="split"
            ).set_index("Task")
        else:
            raise Exception("There are no tasks included in the json data")

        if "resources" in json_dict:
            resources = pd.DataFrame.from_dict(
                json_dict["resources"], orient="split"
            ).set_index("Resource")
        else:
            raise Exception("There are no resources included in the json data")

        if "tasks_for_resource" in json_dict:
            tasks_for_resource = pd.DataFrame.from_dict(
                json_dict["tasks_for_resource"], orient="split"
            ).set_index("Resource")
        else:
            raise Exception("There are no tasks for resource included in the json data")

        return cls(tasks, resources, tasks_for_resource)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate that the passed in data is likely to be valid when putting it into
         the model. The current validations that are applied are:

         1. Ensure total task time does not exceed to resource time.
         2. Ensure all tasks have at least one resource who can perform them.

        Returns:
            Tuple[bool, List[str]]: The bool value says whether or not the data is
             valid. The list includes any validation errors that are found.
        """
        is_valid = True
        error_list = []
        if self.tasks.Time.sum() > self.resources.AvailableTime.sum():
            is_valid = False
            error_list.append(
                f"The total time for the tasks, {self.tasks.Time.sum()}, exceeds the "
                f"avialable time for the resources, {self.resources.AvailableTime}, "
                f"therefore the problem is not feasible."
            )

        if len(self.tasks_for_resource.groupby("Task").size().index) < len(
            self.tasks.index
        ):
            is_valid = False
            missing_tasks = ",".join(
                [
                    str(t)
                    for t in list(
                        set(self.tasks.index)
                        - set(self.tasks_for_resource.groupby("Task").size().index)
                    )
                ]
            )
            error_list.append(
                f"The following tasks do not have any resources that can "
                f" perform them and thus the model is infeasible: {missing_tasks}"
            )
        return (is_valid, error_list)

    def transform_to_model_data(self) -> ModelData:
        """This function will do any data transforms needed and convert the raw data
         into a format that the model wants to use.

        Returns:
            ModelData: Instance of ModelData that is used in the model.
        """
        tasks_for_resource: pd.DataFrame = self.tasks_for_resource.merge(
            self.tasks, how="left", left_on="Task", right_index=True
        )
        tasks_for_resource = tasks_for_resource.merge(
            self.resources[["CostPerHour"]],
            how="left",
            left_on="Resource",
            right_index=True,
        )

        tasks_for_resource["Cost"] = (
            tasks_for_resource.CostPerHour * tasks_for_resource.Time
        )
        return ModelData(
            self.tasks[["Time"]],
            self.resources[["AvailableTime"]],
            tasks_for_resource[["Cost"]],
        )


@dc.dataclass
class SolutionData:
    build_time: float
    solve_time: float
    assignments: pd.DataFrame
