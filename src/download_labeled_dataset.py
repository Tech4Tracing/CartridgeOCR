
# azureml-core of version 1.0.72 or higher is required
# azureml-dataprep[pandas] of version 1.1.34 or higher is required
# azureml-contrib-dataset of version 1.0.72 or higher is required
# TODO: write the annotations as a COCO dataset.

from azureml.core import Workspace, Dataset
import azureml.contrib.dataset
from torchvision.transforms import functional as F

import secrets

from azureml.core.authentication import InteractiveLoginAuthentication
interactive_auth = InteractiveLoginAuthentication(tenant_id=secrets.tenant_id)
#from azureml.core.authentication import AzureCliAuthentication
#cli_auth = AzureCliAuthentication()

workspace = Workspace(secrets.subscription_id, secrets.resource_group, workspace_name, auth=interactive_auth)

dataset = Dataset.get_by_name(workspace, name='imagesforlabeling') # name='headstampID_20210313_041624')
dataset.download(target_path='../data/dataset', overwrite=True)
#dataset.to_pandas_dataframe()
#df=dataset.to_pandas_dataframe()
#df.to_json('../data/dataset/aml_annotations.json', orient='records')

#pytorch_dataset = dataset.to_torchvision()
#img = pytorch_dataset[0][0]
#print(type(img))

# use methods from torchvision to transform the img into grayscale
#pil_image = F.to_pil_image(img)
#gray_image = F.to_grayscale(pil_image, num_output_channels=3)

#imgplot = plt.imshow(gray_image)