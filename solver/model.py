import dataclasses as dc
from time import time
from typing import Any, List, Tuple, Union

import gurobipy as grb
import pandas as pd

from .data import ModelData, SolutionData


def namer(name: str, ind_val: Union[Tuple, List[Any], str, int]) -> str:
    """Function to name a variable or constraint based on the index
     values and the given base name.

    Args:
        name (str): Base name for variable or constraint
        ind_val (Union[Tuple, List[Any], str, int]): Index for the variable or
         constraint that makes it unique amongst the set for this base name.

    Returns:
        str: Unique name for this variable or constraint.
    """
    if isinstance(ind_val, str) or isinstance(ind_val, int):
        ind_vals = str(ind_val)
    else:
        ind_vals = ",".join([str(i) for i in list(ind_val)])
    ret_val = f"{name}[{ind_vals}]"
    return ret_val


@dc.dataclass
class DemoVariableContainer:
    asign_vars: pd.Series


class DemoModel:
    def __init__(self, model_data: ModelData):
        self.model_data = model_data

    def build_and_solve(self) -> SolutionData:
        """Function used to build and solve the demo model and return the model results.

        Raises:
            Exception: If the model doesn't return a feasible solution the function
             will raise an exception.

        Returns:
            SolutionData: An object that holds the solution data for this solve
        """
        mdl = grb.Model("demo_model")
        st = time()
        vars = self.__build_variables(mdl)

        self.__build_constraints(mdl, vars)

        self.__build_objective_function(
            mdl, self.model_data.tasks_for_resource.Cost, vars.asign_vars
        )
        model_build_time = time() - st

        mdl.write("demo.lp")

        st = time()

        print("Solving Model...")
        mdl.optimize()
        status = mdl.Status
        print(f"\tSolved Model with Status: {status}")
        model_solve_time = time() - st

        solution_df: pd.DataFrame = pd.DataFrame(
            index=vars.asign_vars.index, columns=["IsAssigned"]
        )
        if status == grb.GRB.OPTIMAL:
            print("Solution:")
            print(f"\tObjective value ={mdl.getObjective().getValue()}")
            solution_df["X"] = vars.asign_vars
            for it in solution_df.itertuples():
                solution_df.loc[it.Index, "IsAssigned"] = it.X.X
            solution_df = solution_df.query("IsAssigned > 0.1").drop(columns="X")
        elif status == grb.GRB.INFEASIBLE:
            print("Model results in infeasible solution.")
            raise Exception("Model results in infeasible solution.")

        return SolutionData(model_build_time, model_solve_time, solution_df)

    def __build_variables(self, solver: grb.Model) -> DemoVariableContainer:
        x = pd.Series(
            solver.addVars(
                self.model_data.tasks_for_resource.index, vtype=grb.GRB.BINARY, name="x"
            ),
            index=self.model_data.tasks_for_resource.index,
        )

        return DemoVariableContainer(x)

    def __build_constraints(self, solver: grb.Model, variables: DemoVariableContainer):
        """Builds all of the constraints for the demo model.

        Args:
            solver (grb.Model): The solver being used in this model.
            variables (DemoVariableContainer): The variable container for this model.
        """
        print("Building constraints for the demo model.")
        self.__build_max_work_hours_for_resources_constraints(
            solver,
            self.model_data.tasks.Time,
            self.model_data.resources.AvailableTime,
            variables.asign_vars,
        )

        self.__build_can_only_assign_task_to_one_resource_constraints(
            solver, variables.asign_vars
        )
        print("Finished building constraints for demo model.")

    def __build_max_work_hours_for_resources_constraints(
        self,
        solver: grb.Model,
        task_hours: pd.Series,
        resource_hours_allowed: pd.Series,
        assign_vars: pd.Series,
    ):
        """Function to build constraints that ensure each resource doesn't work
         more than their maximum time in the model.

        Args:
            solver (grb.Model): The solver being used in this model
            task_hours (pd.Series): Series that has the length of time that
             each task takes.
            resource_hours_allowed (pd.Series): Series that has the length of time
             that each resource is allowed to work.
            assign_vars (pd.Series): Resource to task assignment variables.
        """
        print("\tBuilding constraints for setting max work hours for resources.")
        cons_df = assign_vars.to_frame("x").merge(
            task_hours.to_frame("eta"), how="left", left_on="Task", right_index=True
        )
        cons_df["sum_eta_dot_x"] = cons_df.eta * cons_df.x
        cons_df = cons_df[["sum_eta_dot_x"]].groupby("Resource").sum()
        cons_df = cons_df.merge(
            resource_hours_allowed.to_frame("gamma"),
            how="left",
            left_index=True,
            right_index=True,
        )

        for it in cons_df.itertuples():
            solver.addConstr(
                it.sum_eta_dot_x <= it.gamma,
                name=namer("MaxHoursForResource", it.Index),
            )
        solver.update()
        print(f"\t\tAdded {len(cons_df)} max hours for resource constraints.")

    def __build_can_only_assign_task_to_one_resource_constraints(
        self, solver: grb.Model, assign_vars: pd.Series
    ):
        """Function to build the constraints for ensuring that each task is assigned
         to exactly one resource.

        Args:
            solver (grb.Model): Model solver object to add the constraints to
            assign_vars (pd.Series): Resource to task assignment variables.
        """
        print(
            "\tBuilding constraints for limiting tasks to only be assigned "
            "to one resource."
        )
        cons_df = assign_vars.to_frame("sum_over_r_on_x").groupby("Task").sum()
        for it in cons_df.itertuples():
            solver.addConstr(
                it.sum_over_r_on_x == 1,
                name=namer("AssignEachTaskToOneResource", it.Index),
            )
        solver.update()
        print(
            f"\t\tAdded {len(cons_df)} tasks assigned to a single resource constraints."
        )

    def __build_objective_function(
        self, solver: grb.Model, costs: pd.Series, assign_vars: pd.Series
    ):
        """Builds the objective function for this model.

        Args:
            solver (grb.Model): The solver being used in this model to add
             the objective to
            costs (pd.Series): The series of costs for assigning a
             resource to a task
            assign_vars (pd.Series): The assignment variables for the
             resources to tasks
        """
        print("Adding a minimize cost objective function to the model.")
        obj = costs * assign_vars
        solver.setObjective(grb.quicksum(obj), grb.GRB.MINIMIZE)
