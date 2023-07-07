from fastapi import FastAPI
from pydantic import BaseModel
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.callbacks import get_openai_callback
from azure.storage.blob import BlobServiceClient, BlobClient
import os


def read_text_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            text = file.read()
        return text
    except Exception as e:
        print(f"Error reading file '{file_path}': {str(e)}")
        return None

def read_text_from_blob(container_name, blob_name):
    try:
        connection_string = "DefaultEndpointsProtocol=https;AccountName=azuretestshubham832458;AccountKey=2yEaP59qlgKVv6kEUCA5ARB4wdV3ZRoL2X9zjYCcIxOSYAG1CSBbBlAMPx3uBIe7ilQtSh7purEK+AStvFn8GA==;EndpointSuffix=core.windows.net"  # Replace with your Azure Blob Storage connection string
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container="transcript", blob=blob_name)
        blob_data = blob_client.download_blob().readall()
        return blob_data.decode('utf-8')
    except Exception as e:
        print(f"Error reading blob '{blob_name}': {str(e)}")
        return None

app = FastAPI()
destination_path='transcripts'
class DownloadPayload(BaseModel):
    blob_name: str

def download_file_from_blob(container_name, blob_name):
    try:
        connection_string = "DefaultEndpointsProtocol=https;AccountName=azuretestshubham832458;AccountKey=2yEaP59qlgKVv6kEUCA5ARB4wdV3ZRoL2X9zjYCcIxOSYAG1CSBbBlAMPx3uBIe7ilQtSh7purEK+AStvFn8GA==;EndpointSuffix=core.windows.net"  # Replace with your Azure Blob Storage connection string
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        destination_path = f"transcripts/{blob_name}"  # Replace with the desired destination path
        
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)  # Create the destination directory if it doesn't exist
        
        with open(destination_path, "wb") as file:
            file.write(blob_client.download_blob().readall())
        
        print(f"File downloaded successfully: {destination_path}")
        return True
    except Exception as e:
        print(f"Error downloading file '{blob_name}': {str(e)}")
        return False

@app.post("/download")
def download_file(payload: DownloadPayload):
    blob_name = payload.blob_name
    
    success = download_file_from_blob("transcript", blob_name)
    
    if success:
        return {"message": "File download completed successfully."}
    else:
        return {"message": "File download failed."}
    
os.environ["OPENAI_API_KEY"] = "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"

class Question(BaseModel):
    question: str

class DownloadPayload(BaseModel):
    blob_name: str

def search_questions(questions, context):
    pdf_directory = "./transcripts/"
    loader = PyPDFDirectoryLoader(pdf_directory)
    docs = loader.load()
    index = VectorstoreIndexCreator().from_loaders([loader])
    output_data = []
    total_cost = 0  # Initialize total cost
    with get_openai_callback() as cb:
        for i, question in enumerate(questions):
            full_question = f"{context} {question}"  # Add the context before each question
            answer = index.query_with_sources(full_question)
            output_data.append(answer)
        total_cost = cb.total_cost  # Get the total cost from the callback
    return output_data

    
context=read_text_from_file('context.txt')
print(context)
@app.post("/predict")
def predict(payload: Question):
    question = payload.question
    answer = search_questions([question], context)[0]  # Pass the context as an argument
    return {"answer": answer['answer'], "source": answer['sources']}

