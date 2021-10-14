from azureml.core import Workspace, Environment
from azureml.core.webservice import AciWebservice
from azureml.core.model import InferenceConfig, Model

ws = Workspace.from_config()
model = Model(ws, 'APImodel')


env = Environment(name='myenv')
python_packages = ['Pillow', 'numpy', 'azureml-core', 'torch', 'torchvision', 'pycocotools', 'azureml-sdk', 'azure-storage-blob']
for package in python_packages:
    env.python.conda_dependencies.add_pip_package(package)
dummy_inference_config = InferenceConfig(
    environment=env,
    source_directory=".",
    entry_script="predictions/score.py",
)

deployment_config = AciWebservice.deploy_configuration(
        cpu_cores=1,
        memory_gb=8,
    )

service = Model.deploy(
    ws,
    "cartridge-ocr",
    [model],
    dummy_inference_config,
    deployment_config,
    overwrite=True,
)
service.wait_for_deployment(show_output=True)

print(service.get_logs())