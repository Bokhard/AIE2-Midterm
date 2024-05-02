import chainlit as cl
from app_langchain import RetrievalAugmentedChat

# Run via `chainlit run app.py -w`

# Global variable to hold the RetrievalAugmentedChat instance
retrieval_chat = None

@cl.on_chat_start  
# marks a function that will be executed at the start of a user session
async def start_chat():
    global retrieval_chat
    try: 
        # pdf_document_path = "DataRepository/meta10k.pdf"
        pdf_document_path = 'https://d18rn0p25nwr6d.cloudfront.net/CIK-0001326801/c7318154-f6ae-4866-89fa-f0c589f2ee3d.pdf'
        basic_model = "gpt-3.5-turbo"
        basic_embedding_model = "text-embedding-3-small"
        retrieval_chat = RetrievalAugmentedChat(pdf_document_path, basic_model, basic_embedding_model)
        retrieval_chat.load_doc_to_vectorstore()
        await cl.Message("Ok all set. Please type your query about Meta's 10-K report.").send()
    except Exception as e:
        await cl.Message(f"An error occurred during initialization: {str(e)}").send()

@cl.on_message  
# marks a function that should be run each time the chatbot receives a message from a user
async def main(message: cl.Message):
    global retrieval_chat
    try: 
        if retrieval_chat is None:
            await cl.Message("The retrieval system is not initialized. Please restart the chat.").send()
            return
        
        question = message.content
        response = retrieval_chat.query_and_return_answers(question)
        await cl.Message(response).send()
    except Exception as e:
        await cl.Message(f"An error occurred while processing your query: {str(e)}").send()