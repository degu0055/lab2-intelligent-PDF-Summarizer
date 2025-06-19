
# Intelligent PDF Summarizer

This app shows how to use Azure Durable Functions to make smart apps that process documents like PDFs. It works step by step because the output from one step goes to the next. This is important so the app does not repeat expensive calls if there is a problem.

The app uses different Azure services:  
- Azure Durable Functions  
- Azure Storage  
- Azure Cognitive Services  
- Azure Open AI  

## How it works

1. You upload PDFs to a special storage container.  
2. The app starts automatically when a PDF is uploaded.  
3. It downloads the PDF.  
4. It uses Azure Cognitive Service to read the PDF text.  
5. Then, it sends the text to Azure Open AI to understand and summarize the PDF content.  
6. The summary is saved as a new file and uploaded to another storage container.  

## What you need to run the app locally

- An active Azure subscription  
- Python 3.9 or higher  
- Azure Functions Core Tools installed  
- Permission to use Azure OpenAI  
- Azurite storage emulator to simulate storage locally  

You also need to set up a file called **local.settings.json** with your Azure service details.

## Running the app

- Start Azurite to simulate storage.  
- Install the Python packages needed with this command:  
  ```bash
  python3 -m pip install -r requirements.txt
  ```  
- Create two storage containers named `input` and `output`.  
- Run the function app locally:  
  ```bash
  func start --verbose
  ```  
- Upload PDFs to the `input` container.  
- After some time, check the `output` container for the summarized PDF files.

**Note:** The summaries may be short because of limits in the AI service, which helps keep costs low.

---

## Video Demo

Watch the demo video here: [Demo Video Link](https://drive.google.com/file/d/1rWNZP-3pJOjBIsDDh9_2CDi3VH-f8-Bd/view?usp=sharing)  
