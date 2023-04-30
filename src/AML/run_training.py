import sys
from azureml.core import Workspace, Experiment, Environment, ScriptRunConfig
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from shutil import copy

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
copy('./config.json', 'model/config.json')

myenv = Environment.from_pip_requirements(name="myenv",
                                          #file_path="requirements.txt"
                                          file_path="model/src/t4t_headstamp.egg-info/requires.txt")

myenv.environment_variables['PYTHONPATH'] = './model/src/t4t_headstamp'
myenv.environment_variables['RUNINAZURE'] = 'true'

config = ScriptRunConfig(source_directory=src_dir,
                         script="./src/t4t_headstamp/training/train.py",
                         arguments=sys.argv[1:] if len(sys.argv) > 1 else None,
                         compute_target=cpu_cluster_name, environment=myenv)

run = experiment.submit(config)
aml_url = run.get_portal_url()
print(aml_url)
