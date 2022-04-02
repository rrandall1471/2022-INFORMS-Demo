---
title:  2020 INFORMS Demo Formulation
author: Rob Randall, PhD Princeton Consultants
date: \today
header-includes: |
    \usepackage{amssymb}
    \usepackage{fancyhdr}
    \usepackage{graphicx}
    \pagestyle{fancy}
    \usepackage{underscore}
geometry: margin=1in
---

## 1 Data

### 1.1 Sets

* Let $\mathcal T$ be the set of tasks that need to be completed.
* Let $\mathcal G$ be the set of resource groups.
* Let $\mathcal R$ be the set of resources that can complete the tasks.
* Let $\mathcal Q_r$ be the set of tasks that resource $r\in\mathcal R$ can perform.
* Let $\mathcal P_t$ be the set of resources that a task $t\in\mathcal T$ can be assigned to.
* Let $\mathcal S_g$ be the set of resources that belong to resource group $g \in\mathcal G$.

### 1.2 Data Inputs

* Let $\eta_t \ge 0$ be the number of hours for a task $t\in\mathcal T$.
* Let $\lambda_r \ge 0$ be the cost per hour for a resource $r\in\mathcal R$.
* Let $\gamma_r \ge 0$ be the number of hours that a resource $r\in\mathcal R$ can work in one day.
* Let $\alpha_g \ge 0$ be the minimum number of tasks, $t\in\mathcal T$, that a resource group $g\in\mathcal G$ can work in one day.
* Let $\beta_g \ge 0$ be the maximum number of tasks, $t\in\mathcal T$, that a resource group $g\in\mathcal G$ can work in one day.

### 1.3 Data Transformations

* Let $\theta_{rt}$ be the cost for a resource $r\in\mathcal R$ performing a task $t\in\mathcal T$.

$$ \theta_{rt} = \eta_t \cdot \lambda_r \qquad\forall r\in\mathcal R,\,t\in\mathcal T$$

## 2 Decision Variables

* Let $x_{rt}\in\{0, 1\}$ be one if the resource $r\in\mathcal R$ is assigned to perform task $t\in\mathcal T$, 0 otherwise.
* Let $y_g\in \mathbb{Z} \ge 0$ be the number of tasks assigned to resources in $g\in\mathcal G$.

## 3 Constraints

### 3.1 Assign Each Task to only One Resource

Each task can only be assigned to be performed one task in the model.

$$\sum_{r\in\mathcal R} x_{rt} = 1 \qquad\forall t\in\mathcal T$$

### 3.2 Ensure Each Resource Stays within their Allowed Hours

Each resource can only be assigned tasks whose total time must be no more than their maximum hours for a day.

$$\sum_{t\in\mathcal T} \eta_t \cdot x_{rt} \le \gamma_r \qquad\forall r\in\mathcal R$$

### 3.3 Count Tasks Assigned to Resource Group

Determine the number of tasks assigned to resources in each resource group

$$\sum_{r\in\mathcal S_g}\sum_{t\in\mathcal Q_r} x_{rt} = y_g \qquad\forall g \in\mathcal G$$

### 3.4 Resource Groupss are Task Count Limited

#### 3.4.1 Ensure Resource Group Meets Minimum Task Processing

Ensure each resource group is only scheduled up to its maximum number of tasks

$$y_g \ge \alpha_g \qquad\forall g\in\mathcal G$$

#### 3.4.2 Ensure Resource Group Meets Maximum Task Processing

Ensure each resource group is only scheduled up to its maximum number of tasks

$$y_g \le \beta_g \qquad\forall g\in\mathcal G$$

## 4 Objective

The objective function for the model is to minimize the cost of assigning the resources to tasks.

$$\text{Minimize}\,\sum_{r\in\mathcal R}\sum_{t\in\mathcal T} \theta_{rt}\cdot x_{rt}$$
