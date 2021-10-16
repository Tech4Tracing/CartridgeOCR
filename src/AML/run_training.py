from azureml.core import Workspace, Experiment, Environment, ScriptRunConfig, environment
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException

ws = Workspace.from_config()

# Choose a name for your CPU cluster
# cpu_cluster_name = "cpucluster"
cpu_cluster_name = "gpucompute"
experiment_name = "main"
src_dir = "model"
script = "train.py"

# Verify that cluster does not exist already
try:
    cpu_cluster = ComputeTarget(workspace=ws, name=cpu_cluster_name)
    print('Found existing cluster, use it.')
except ComputeTargetException:
    compute_config = AmlCompute.provisioning_configuration(vm_size='Standard_DS12_v2',
                                                           max_nodes=4)
    cpu_cluster = ComputeTarget.create(ws, cpu_cluster_name, compute_config)

cpu_cluster.wait_for_completion(show_output=True)


experiment = Experiment(workspace=ws, name=experiment_name)


myenv = Environment.from_pip_requirements(name = "myenv",
                                          file_path = "requirements.txt") 

myenv.environment_variables['PYTHONPATH'] = './src'
myenv.environment_variables['RUNINAZURE'] = 'true'

config = ScriptRunConfig(source_directory=src_dir, script="./training/train.py", compute_target=cpu_cluster_name, environment=myenv)

run = experiment.submit(config)
aml_url = run.get_portal_url()
print(aml_url)
