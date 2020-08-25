import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    print("Azure Blob storage v12 - Python quickstart sample")
    connect_str = os.getenv('BLOB_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    container_list = blob_service_client.list_containers()
    for c in container_list:
        print(c)

    container_client = blob_service_client.get_container_client("deathstar-media")
    blob_list = container_client.list_blobs()
    for blob in blob_list:
            print("\t" + blob.name)

    return req
