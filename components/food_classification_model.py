from kfp.v2.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Metrics,
)

# snapshot component
@component(
  base_image="tensorflow/tensorflow:2.11.0",
  packages_to_install=["tensorflow_hub"]
)
def train_model(
  epochs: int, 
  batch_size: int, 
  learning_rate: float, 
  model_pvc_name: str,
  model_dir: str,
  model_name: str,
  run_id: str
  ) -> None:
  
  import os
  import tensorflow as tf
  import tensorflow_hub as hub
  from tensorflow.python.keras.models import load_model

  # enable eager mode
  tf.compat.v1.enable_eager_execution()

  # print hyper-parameters
  print("epochs: " + str(epochs))
  print("batch_size: " + str(batch_size))
  print("learning_rate: " + str(learning_rate))
  print(model_pvc_name)

  # load model from tensorflow hub
  # m = hub.KerasLayer('https://tfhub.dev/google/aiy/vision/classifier/food_V1/1')
  model = tf.keras.Sequential([hub.KerasLayer('https://tfhub.dev/google/aiy/vision/classifier/food_V1/1')])

  # building model
  model.build(input_shape=(None, 192, 192, 3))
  model.summary()

  # saving model
  os.mkdir(os.path.join(model_dir, run_id))
  model_path = os.path.join(model_dir, run_id, model_name + ".h5")
  model.save(model_path)

  return None