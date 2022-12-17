"""
Demonstration of MLOps pipeline with NetApp DataOps Toolkit
"""
import kfp
import kfp.dsl as dsl
import kfp.onprem as onprem
from kfp.v2.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Metrics,
)

"""
Import re-usable components
"""
from components import netapp_snapshot
from components import food_classification_model

"""
Declare pipeline specific components
""" 

# data preprocessing component
@component
def data_preprocessing() -> None:
  
  return None

# model validation component
@component
def validate_model() -> str:
  validation_result = "passed"
  return validation_result

# pushing model component
@component
def push_model() -> None:
  return None

# pushing model component
@component
def deploy_model() -> None:
  return None

"""
Building pipeline DAG
""" 
@dsl.pipeline(
    name="AI Training Run",
    description="Template for executing an AI training run with built-in training dataset traceability and trained model versioning",
)
def ai_training_run(
  epochs: int=1,
  batch_size: int=64,
  learning_rate: float=0.001,
  dataset_pvc_name: str="dataset",
  model_pvc_name: str="model",
  kubeflow_user_namespace: str="kubeflow-user-example-com",
  volume_snapshot_class :str="csi-snapclass",
):
  dataset_dir = "/mnt/dataset"
  model_dir = "/mnt/model"
  model_name = "food-classfier"

  # STEP1: Taking snapshot before data preprocessing 
  snapshot_before_preprocessing = netapp_snapshot.create_snapshot(
    namespace=kubeflow_user_namespace, 
    pvc_name=dataset_pvc_name, 
    volume_snapshot_class=volume_snapshot_class
    )

  # STEP2: proprocessing dataset
  preprocess_data_task = data_preprocessing().after(snapshot_before_preprocessing)
  preprocess_data_task.apply(
    onprem.mount_pvc(dataset_pvc_name, 'datavol', dataset_dir)
  )

  # STEP3: Taking snapshot after data preprocessing
  snapshot_after_preprocessing = netapp_snapshot.create_snapshot(
    namespace=kubeflow_user_namespace, 
    pvc_name=dataset_pvc_name, 
    volume_snapshot_class=volume_snapshot_class
    ).after(preprocess_data_task)  

  # STEP4: Training model
  train_task = food_classification_model.train_model(
    epochs=epochs, 
    batch_size=batch_size, 
    learning_rate=learning_rate,
    model_pvc_name=model_pvc_name,
    model_dir=model_dir,
    model_name=model_name,
    run_id = kfp.dsl.RUN_ID_PLACEHOLDER,
    ).after(snapshot_after_preprocessing)
  train_task.apply(
    onprem.mount_pvc(model_pvc_name, 'modelvol', model_dir)
  )

  # STEP5: Validating model
  validate_task = validate_model().after(train_task)

  # Checking if validation accuracy is heiger than target score
  with kfp.dsl.Condition(
    validate_task.output=="passed", "validation-result"
    ): 
    # STEP6: Push model to ONTAP S3
    push_task = push_model()

    # STEP7: Deploy model
    deploy_task = deploy_model().after(push_task)
  

"""
Compile a pipeline using the v2 compatible mode
"""
kfp.compiler.Compiler(mode=kfp.dsl.PipelineExecutionMode.V2_COMPATIBLE).compile(
    pipeline_func=ai_training_run,
    package_path='ai-training-run.yaml')