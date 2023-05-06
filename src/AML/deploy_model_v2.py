import argparse
import os
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
    Environment,
    CodeConfiguration,
    BuildContext
)
from azure.identity import DefaultAzureCredential

parser = argparse.ArgumentParser()
parser.add_argument('--service', required=True, choices=['managed', 'aks', 'aci', 'local'])
parser.add_argument('--update', default=False)
parser.add_argument('--model', default='khaki_pear_lite')
args = parser.parse_args()




ml_client = MLClient.from_config(
    DefaultAzureCredential()
)

#model = Model(name="APImodel", version="7")

os.system("cp -a model AML/deployment_dockerfile/")
env = Environment(name='myenv', 
                  build=BuildContext(path="AML/deployment_dockerfile/")
                 )                  
ml_client.environments.create_or_update(env)
#dummy_inference_config = InferenceConfig(
#    environment=env,
#    source_directory="./model/src/t4t_headstamp",
#    entry_script="predictions/score.py",
#)

endpoint_name = 'cartridgeocrmanaged'
endpoint = ManagedOnlineEndpoint(
    name = endpoint_name, 
    description="endpoint for headstamp detection",
    auth_mode="key"
)
deployment = ManagedOnlineDeployment(
    name="dev",
    endpoint_name=endpoint_name,
    model="APImodel:7" if args.service == "managed" else Model(name="APIModel", path="/mnt/c/GitHub/CartridgeOCR/data/models/khaki_pear_lite/"), 
    environment=env,
    code_configuration=CodeConfiguration(
        code="./model/src/", scoring_script="t4t_headstamp/predictions/score.py"
    ),
    instance_type="Standard_DS3_v2",
    instance_count=1,
)

if args.service == 'managed':
    
    ml_client.online_endpoints.begin_create_or_update(endpoint).wait()
    ml_client.online_deployments.begin_create_or_update(deployment).wait()
    endpoint.traffic = {"dev": 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).wait()
    #ml_client.online_endpoints.get(name=endpoint_name)


elif args.service == 'aci':
    raise "aci unsupported"

elif args.service == 'local':
    ml_client.online_endpoints.begin_create_or_update(endpoint, local=True)
    ml_client.online_deployments.begin_create_or_update(deployment, local=True)
    print(ml_client.online_endpoints.get(name=endpoint_name, local=True))

else:
    raise "todo"
    assert(args.service == 'aks')
    version_name = 'version1'
    endpoint_name = 'cartridgeocraks'
    compute = ComputeTarget(ws, 'cartridgeocraks')

    if args.update:
        # Retrieve existing service.
        service = Webservice(name=endpoint_name, workspace=ws)

        # Update to new model(s).
        print('deleting '+endpoint_name)
        service.delete()

        # service.update(models=[model], inference_config=dummy_inference_config)
    print('Deploying...')
    deployment_config = AksEndpoint.deploy_configuration(cpu_cores=1, memory_gb=8,
                                                            enable_app_insights=False,  # True,
                                                            # tags={'sckitlearn': 'demo'},
                                                            description="testing versions",
                                                            version_name=version_name,
                                                            traffic_percentile=100)
    service = Model.deploy(ws, endpoint_name, [model], dummy_inference_config, deployment_config, compute)

#service.wait_for_deployment(show_output=True)
#print(service.state)
#print(service.get_logs())
