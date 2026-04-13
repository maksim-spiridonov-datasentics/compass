# Databricks notebook source
# MAGIC %pip install -q databricks-openai databricks-agents

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

UC_MODEL_NAME = dbutils.widgets.get("uc_model_name")
ENDPOINT_NAME = dbutils.widgets.get("endpoint_name")
SCALE_TO_ZERO = dbutils.widgets.get("scale_to_zero") == "True"

# COMMAND ----------

import sys

current_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
src_path = current_path.replace("deploy_notebook", "src")

if "Users" in current_path:
    src_path = f"/Workspace{src_path}"

print(src_path)

sys.path.append(src_path)

# COMMAND ----------

# DBTITLE 1,Untitled
from databricks import agents
import mlflow
from src.compass import AICompass

agent = AICompass()
mlflow.models.set_model(agent)

input_example = [
    {"role": "user", "content": "I would like to automate invoice extraction for the financial department"}
]

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")

with mlflow.start_run():
    mlflow.pyfunc.log_model(
        name = "test_ai_compass",
        code_paths=[
            f"{src_path}/prompts.py",
            f"{src_path}/compass.py",
        ],
        python_model=f"{src_path}/compass.py",
        pip_requirements=["databricks-openai==0.11.1"],
        input_example=input_example,
    )
    run_id = mlflow.last_active_run().info.run_id


model_uri = f"runs:/{run_id}/test_ai_compass"

registered = mlflow.register_model(model_uri, UC_MODEL_NAME)
print("Registered:", registered.name, "version:", registered.version)

# COMMAND ----------

# DBTITLE 1,Untitled
deployment = agents.deploy(
    model_name=UC_MODEL_NAME,
    model_version=registered.version,
    scale_to_zero=SCALE_TO_ZERO,
    endpoint_name=ENDPOINT_NAME,
    workload_size="Small"
)

print("Endpoint:", deployment.endpoint_name)
print("URL:", deployment.query_endpoint)
