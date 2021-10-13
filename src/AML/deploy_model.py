"""This module does the deployment to a new or existing web service in the current environment"""
import os

from azureml.core.environment import Environment
from azureml.core.model import InferenceConfig, Model
from azureml.core.webservice import AciWebservice

from aml_interface import AMLInterface
from dotenv import load_dotenv


__here__ = os.path.dirname(__file__)


def get_inference_config(aml_interface, aml_env_name):
    """Gets AML Interface from aml_interface.py and set environment/workspace"""
    aml_env = Environment.get(
        workspace=aml_interface.workspace,
        name=aml_env_name
    )
    scoring_script_path = 'predictions/score.py'
    inference_config = InferenceConfig(
        entry_script=scoring_script_path,
        environment=aml_env,
        source_directory="src"
    )
    return inference_config


def deploy_service(aml_interface, aml_env_name, model_name, deployment_service_name):
    """New deployment of ACIwebservice, configuration, model and service"""
    inference_config = get_inference_config(aml_interface, aml_env_name)
    deployment_config = AciWebservice.deploy_configuration(
        cpu_cores=1,
        memory_gb=1,
    )
    model = aml_interface.workspace.models.get(model_name)
    service = Model.deploy(
        aml_interface.workspace,
        deployment_service_name,
        [model],
        inference_config,
        deployment_config,
        )
    service.wait_for_deployment(show_output=True)
    print(service.scoring_uri)


def update_service(aml_interface, aml_env_name, deployment_service_name, model_name):
    """Existing Webservice updates on deployment"""
    inference_config = get_inference_config(aml_interface, aml_env_name)
    service = AciWebservice(
        name=deployment_service_name,
        workspace=aml_interface.workspace
    )
    model = aml_interface.workspace.models.get(model_name)
    service.update(models=[model], inference_config=inference_config)
    print(service.state)
    print(service.scoring_uri)


def main():
    """Sets local and library vars and checks if webservice exists"""
    load_dotenv()
    # Retrieve vars from env
    workspace_name = os.environ['AML_WORKSPACE_NAME']
    
    resource_group = os.environ['RESOURCE_GROUP']
    subscription_id = os.environ['SUBSCRIPTION_ID']
    tenant_id = os.environ['TENANT_ID']
    client_id = os.environ['CLIENT_ID']
    print(client_id)
    client_secret = os.environ['CLIENT_SECRET']
    model_name = os.environ['MODEL_NAME']
    deployment_service_name = os.environ['DEPLOYMENT_SERVICE_NAME']
    aml_env_name = os.environ['AML_ENV_NAME']

    aml_secrets = {
        'tenant_id': tenant_id,
        'client_id': 'a089df0b-fbee-4530-8440-e1c3c408bd3b',
        'client_secret': client_secret,
        'subscription_id': subscription_id,
        'workspace_name': workspace_name,
        'resource_group': resource_group
    }
    aml_interface = AMLInterface(aml_secrets)

    webservices = aml_interface.workspace.webservices.keys()
    if "aciservice" not in webservices:
        deploy_service(aml_interface, aml_env_name, model_name, deployment_service_name)
    else:
        update_service(aml_interface, aml_env_name, deployment_service_name, model_name)


if __name__ == '__main__':
    main()
