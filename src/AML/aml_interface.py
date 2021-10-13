"""This module gathers the workspace/environment and compute check"""
from azureml.core import Workspace
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.exceptions import ComputeTargetException

class AMLInterface:
    """AML environment setup and compute check"""
    def __init__(self, aml_secrets):
        
        auth = ServicePrincipalAuthentication(
            service_principal_id=aml_secrets['client_id'],
            service_principal_password=aml_secrets['client_secret'],
            tenant_id=aml_secrets['tenant_id']
        )
        print(aml_secrets)
        self.workspace = Workspace(
            workspace_name=aml_secrets['workspace_name'],
            auth=auth,
            subscription_id=aml_secrets['subscription_id'],
            resource_group=aml_secrets['resource_group']
        )

    def register_aml_environment(self, environment):
        """Register the workspace"""
        environment.register(workspace=self.workspace)
    def get_compute_target(self, compute_name, vm_size=None):
        """Checking compute target, if new or existing"""
        try:
            compute_target = ComputeTarget(
                workspace=self.workspace,
                name=compute_name
            )
            print('Found existing compute target')
        except ComputeTargetException:
            print('Creating a new compute target...')
            compute_config = AmlCompute.provisioning_configuration(
                vm_size=vm_size,
                min_nodes=1,
                max_nodes=2
            )
            compute_target = ComputeTarget.create(
                self.workspace,
                compute_name,
                compute_config
            )
            compute_target.wait_for_completion(
                show_output=True,
                timeout_in_minutes=20
            )
        return compute_target
