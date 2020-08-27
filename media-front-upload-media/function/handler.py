import os, sys, io, json
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError
from requests_toolbelt import MultipartDecoder
import base64
import uuid

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
        filename
        file
    """
    payload = json.loads(req)

    if ('filename' not in payload or
       'file' not in payload):
        msg = 'Make sure the input has `filename` and `file`'
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    try:
        [filename, filetype] = payload['filename'].split('.', maxsplit=1)
        [file_info, file_data_b64] = payload['file'].split(',', maxsplit=1)
        file_data_binary = base64.b64decode(file_data_b64) # bytes object
    except Exception as ex:
        msg = 'file base64 not properly encoded. ' + str(ex)
        ret = json.dumps({"status":"InputDataError", "message":msg})
        sys.exit(msg)

    file_data_binary_stream = io.BytesIO(file_data_binary)

    try:
        connect_str = os.getenv('BLOB_STORAGE_CONNECTION_STRING')
        container_name = os.getenv('CONTAINER_NAME')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(container_name)

        filename = filename + '-' + uuid.uuid4().hex
        blobname = filename + '.' + filetype

        blob_client = blob_service_client.get_blob_client(container=container_name,
                blob=blobname)

        ret = blob_client.upload_blob(file_data_binary_stream)

        return json.dumps({"status":"success", "media_id": filename, "media_type": filetype})

    except ResourceExistsError as ex:
        msg = 'filename ' + str(filename) + ' already exists'
        ret = json.dumps({"status":"FilenameExistsError", "message":msg})
        sys.exit(ret)
    except Exception as ex:
        msg = 'AZure blob storage error: ' + str(ex)
        ret = json.dumps({"status":"StorageBackendError", "message":msg})
        sys.exit(ret)
