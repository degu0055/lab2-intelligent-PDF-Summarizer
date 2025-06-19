import logging
import os
from datetime import datetime

import azure.functions as func
import azure.durable_functions as df
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import requests

my_app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

blob_service_client = BlobServiceClient.from_connection_string(os.environ.get("BLOB_STORAGE_ENDPOINT"))


@my_app.blob_trigger(arg_name="myblob", path="input", connection="BLOB_STORAGE_ENDPOINT")
@my_app.durable_client_input(client_name="client")
async def blob_trigger(myblob: func.InputStream, client):
    logging.info(f"Python blob trigger function processed blob"
                 f"Name: {myblob.name} "
                 f"Blob Size: {myblob.length} bytes")

    blobName = myblob.name.split("/")[1]
    await client.start_new("process_document", client_input=blobName)


@my_app.orchestration_trigger(context_name="context")
def process_document(context):
    blobName: str = context.get_input()

    first_retry_interval_in_milliseconds = 5000
    max_number_of_attempts = 3
    retry_options = df.RetryOptions(first_retry_interval_in_milliseconds, max_number_of_attempts)

    # Download the PDF from Blob Storage and analyze it
    result = yield context.call_activity_with_retry("analyze_pdf", retry_options, blobName)

    # Summarize using OpenAI API
    result2 = yield context.call_activity_with_retry("summarize_text", retry_options, result)

    # Write summary back to Blob Storage
    result3 = yield context.call_activity_with_retry("write_doc", retry_options, {
        "blobName": blobName,
        "summary": result2
    })

    return logging.info(f"Successfully uploaded summary to {result3}")


@my_app.activity_trigger(input_name='blobName')
def analyze_pdf(blobName):
    logging.info(f"in analyze_text activity")
    global blob_service_client

    container_client = blob_service_client.get_container_client("input")
    blob_client = container_client.get_blob_client(blobName)
    blob = blob_client.download_blob().readall()
    doc = ''

    endpoint = os.environ["COGNITIVE_SERVICES_ENDPOINT"]
    api_key = os.environ["COGNITIVE_SERVICES_API_KEY"]

    credential = AzureKeyCredential(api_key)
    document_analysis_client = DocumentAnalysisClient(endpoint, credential)

    poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=blob, locale="en-US")
    result = poller.result().pages

    for page in result:
        for line in page.lines:
            doc += line.content + " "

    return doc.strip()


@my_app.activity_trigger(input_name='results')
def summarize_text(results):
    logging.info(f"in summarize_text activity")

    openai_api_key = os.environ["OPENAI_API_KEY"]
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"Can you summarize what the following text is about?\n\n{results}"
    data = {
        "model": os.environ.get("CHAT_MODEL_DEPLOYMENT_NAME", "gpt-3.5-turbo"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes PDF documents."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    if response.status_code != 200:
        logging.error(f"OpenAI API Error: {response.text}")
        return {"content": "Failed to summarize document."}

    result = response.json()
    summary = result['choices'][0]['message']['content']
    logging.info(f"Summary: {summary}")
    return {"content": summary}


@my_app.activity_trigger(input_name='results')
def write_doc(results):
    logging.info(f"in write_doc activity")
    global blob_service_client
    container_client = blob_service_client.get_container_client("output")

    summary = results['blobName'] + "-" + str(datetime.now())
    sanitizedSummary = summary.replace(".", "-").replace(":", "-")
    fileName = sanitizedSummary + ".txt"

    content = results['summary']['content']
    logging.info("Uploading summary to blob: " + content)

    container_client.upload_blob(name=fileName, data=content)
    return fileName
