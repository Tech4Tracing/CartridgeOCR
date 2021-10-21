from azureml.core import Workspace, Environment
from azureml.core.webservice import AciWebservice, AksEndpoint, LocalWebservice
from azureml.core.compute import ComputeTarget
from azureml.core.model import InferenceConfig, Model
from azureml.core.webservice import Webservice
import argparse
import os
import json

parser = argparse.ArgumentParser()
parser.add_argument('--tail', default=1000, type=int)
#parser.add_argument('--service', required=True, choices=['aks', 'aci', 'local'])
#parser.add_argument('--update', default=False)
#parser.add_argument('--model', default='APImodel')
args = parser.parse_args()

ws = Workspace.from_config()
#model = Model(ws, args.model)
version_name = 'version1'
endpoint_name = 'cartridgeocraks'
compute = ComputeTarget(ws, 'cartridgeocraks')

service = Webservice(name=endpoint_name, workspace=ws)
logs = json.loads(service.get_logs())[version_name]
logs = logs.split('\n')[max(-len(logs), -args.tail):]
print('\n'.join(logs))
