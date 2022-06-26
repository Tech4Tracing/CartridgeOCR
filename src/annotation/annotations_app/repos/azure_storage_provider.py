import datetime
import logging
import os
import uuid

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
)


class AzureStorageProvider:

    def __init__(self, connectionstring: str = None, container_name: str = None):
        if not connectionstring and not container_name:
            # read configuration from env variable
            connectionstring = os.environ.get("STORAGE_AZURE_CONNECTIONSTRING", None)
            container_name = os.environ.get("STORAGE_AZURE_CONTAINERNAME", None)

        if not connectionstring or not container_name:
            raise Exception("You must configure Azure storage first")

        # used for generating SAS links to images, to dump all traffic on Azure
        self.connection_info = {
            key: value
            for key, value in (
                infoitem.split("=", maxsplit=1)
                for infoitem
                in connectionstring.strip().split(";")
                if infoitem
            )
        }

        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(connectionstring)

        # Create the container if doesn't exist (may be ommited if we believe in devops)
        try:
            self.client.create_container(self.container_name)
        except ResourceExistsError:
            pass

    def upload_file(self, user_id: str, incoming_file, filename: str = "file.bin", prefix: str = ""):
        """
        Accepts a Python file (or object behaving like it)
        Saves it to the storage, creating a directory for it if nessesary (as prefix)
        """
        # we have to forge the key
        if "." in filename:
            ext = "." + filename.rsplit(".", maxsplit=1)[1].lower()
        else:
            ext = "bin"
        # TODO: calculate file hash instead of random UUID but it's heavier
        storage_key = (prefix or "") + str(uuid.uuid4())[:8] + ext

        blob_client = self.client.get_blob_client(container=self.container_name, blob=storage_key)
        blob_client.upload_blob(incoming_file)
        return storage_key, blob_client.get_blob_properties()["size"]

    def retrieve_file_buffer(self, storage_key):
        """
        Sync version of file download (won't work well with large files)
        """
        logging.info("Retrieving file %s from storage", storage_key)
        blob_client = self.client.get_blob_client(container=self.container_name, blob=storage_key)
        return blob_client.download_blob().readall()

    def get_file_presigned_link(self, storage_key, content_type):
        """
        https://docs.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob?view=azure-python#azure-storage-blob-generate-blob-sas
        """
        sas = generate_blob_sas(
            account_name=self.connection_info["AccountName"],
            account_key=self.connection_info["AccountKey"],
            container_name=self.container_name,
            blob_name=storage_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=2),
            content_disposition="inline",
            content_type=content_type
        )
        if self.connection_info['BlobEndpoint'] == "http://annotations_objstore:10000/devstoreaccount1":
            # local dev/demo scenario
            host = "http://localhost:10000/devstoreaccount1"
        else:
            host = self.connection_info['BlobEndpoint']
        # TODO: might think about allowing only Azure urls here, so our customers don't get
        # redirected to some bad place if someone changes env variables (host, container)
        # or manages to save bad storage key (we should generate it ourselves)
        # but I'm probably overthinking it
        return f"{host}/{self.container_name}/{storage_key}?{sas}"

    def delete_file(self, storage_key):
        """
        Removes the file if possible
        """
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=storage_key)
            blob_client.delete_blob()
        except ResourceNotFoundError:
            # already deleted or never existed, which is more or less fine for demo
            pass
