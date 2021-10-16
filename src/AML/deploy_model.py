from azureml.core import Workspace, Environment
from azureml.core.webservice import AciWebservice, AksEndpoint
from azureml.core.compute import ComputeTarget
from azureml.core.model import InferenceConfig, Model
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--service', required=True, choices=['aks', 'aci'])
args = parser.parse_args()

ws = Workspace.from_config()
model = Model(ws, 'APImodel')


env = Environment(name='myenv')
python_packages = ['Pillow', 'numpy', 'azureml-core', 'torch', 'torchvision', 'pycocotools', 'azureml-sdk', 'azure-storage-blob']
for package in python_packages:
    env.python.conda_dependencies.add_pip_package(package)

dummy_inference_config = InferenceConfig(
    environment=env,
    source_directory="./model",
    entry_script="predictions/score.py",    
)

if args.service == 'aci':
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
else:
    assert(args.service == 'aks')
    version_name = 'version1'
    endpoint_name = 'cartridgeocraks'
    compute = ComputeTarget(ws, 'cartridgeocraks')
    deployment_config = AksEndpoint.deploy_configuration(cpu_cores=1, memory_gb=8,
                                                         enable_app_insights=False,  # True,
                                                         tags={'sckitlearn': 'demo'},
                                                         description="testing versions",
                                                         version_name=version_name,
                                                         traffic_percentile=100)
    service = Model.deploy(ws, endpoint_name, [model], dummy_inference_config, deployment_config, compute)

service.wait_for_deployment(show_output=True)

print(service.get_logs())
