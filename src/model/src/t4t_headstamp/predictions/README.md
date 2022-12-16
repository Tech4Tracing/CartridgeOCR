# Layout

- `score.py`: entry point for deployed models hosted in the cloud.
- `inference.py`: main business logic for inference
- `predict.py`: code for running local predictions.  

# Run the model locally

Use `predict.py` as follows:
```
predict.py [-h] [--modelfolder MODELFOLDER] \ 
   [--checkpoint CHECKPOINT] \
   [--render_images boolean] \
   input_file_or_folder output_json
```

# Register the Model in Azure ML
There's 2 methods to register a model in Azure ML:
- programmatically using the Azure ML SDK
- manually through the UI

This makes the model available to use in other places, such as in an endpoint. It's basically a collection of files. In our case, it's used to store the checkpoint of the model, that we use to load up the configuration.

## Using the Azure ML SDK
This is a sample of the code to register a model in your Azure ML workspace, which can also be found at the end of `training/train.py`.

```Python
from azureml.core import Workspace, Datastore, Dataset
from azureml.core.model import Model

ws = Workspace.from_config()

logging.info("Registering Model")
model = Model.register(model_name="modelname",
                    model_path="path where model lives",
                    description="",
                    workspace=ws)
```

You'll need to download the Workspace configuration if running locally. You can find it by going to the Machine Learning workspace in Azure Portal, then in the overview it's next to the delete button as `Download config.json`.

## Using the Azure Portal UI
- Make sure you have a copy of the model downloaded on your local device.
- Open the Machine Learning studio in Azure
- Go to the models tab (looks like a cube)
- Click register model and fill out the information
   - The framework is PyTorch, version 1.8.0


# Deploying the model to an endpoint
There's also 2 methods to do this:
- programmatically using the Azure ML SDK
- manually through the UI

Either way, you'll need 2 things: the model registered in Azure, and a scoring file (`predictions/score.py`). The scoring file should have `init()` and `run(request)` functions. See https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-and-where?tabs=python for more details.

When configuring the deployment, make sure to set CPUs=1 and Memory=8 so it's able to run the code.

## Using the SDK
We use this method in `AML/deploy_model.py` to deploy the model. In this way, you'll need to declare the Conda dependencies.

## Using the Azure Portal UI
- Create a Conda dependencies file using this command `conda env export > conda_env.yml`
- Open the Machine Learning studio in Azure
- Go to the models tab (looks like a cube)
- Click on your model then hit Deploy > Deploy to Web Service
- Fill out the info
   - Compute type should be Azure Container Instance
   - The entry script is the scoring file (predictions/score.py)
   - The Conda dependencies file is the `conda_env.yml` file that you created earlier
   - Click advanced and set CPU=1 and Memory=8
- Hit Deploy
- You'll be able to check on the status by going to the Endpoints tab