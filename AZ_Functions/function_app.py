import logging
import os
from azure.storage.blob import BlobServiceClient
from PIL import Image
import azure.functions as func
import io
from pathlib import Path
 
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
 
@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
 
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')
 
    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
   
 
 
# Set up Azure Storage connection
CONNECTION_STRING = os.getenv("AzureWebJobsStorage")
SOURCE_CONTAINER = "products"
DESTINATION_CONTAINER = "resized-products"
@app.blob_trigger(arg_name="myblob", path="products",
                               connection="AzureWebJobsStorage")
def BlobTrigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")
    logging.info("Blob Triggered!")

    try:
        # Read image from the blob
        image = Image.open(myblob)
 
        # Resize the image to 100x100
        image = image.resize((100, 100))
        logging.info("Resized")
        # Save image to a byte stream
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
 
          # Extract filename and extension
        original_filename = Path(myblob.name).stem  # Extracts filename without extension
        extension = Path(myblob.name).suffix  # Extracts file extension
 
        # Create new filename with '_thumb' suffix
        new_filename = f"{original_filename}_thumb{extension}"
        logging.info("saved image and renamed")
        # Upload resized image to destination container
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=DESTINATION_CONTAINER, blob=new_filename)
        blob_client.upload_blob(img_bytes, blob_type="BlockBlob", overwrite=True)
 
        logging.info(f"Resized image saved as: {new_filename}")
 
    except Exception as e:
        logging.error(f"Error processing image {myblob.name}: {str(e)}")