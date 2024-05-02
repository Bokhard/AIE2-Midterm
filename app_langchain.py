from dotenv import load_dotenv
import os
import logging
import sys
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_core.prompts import ChatPromptTemplate
from operator import itemgetter
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.document_loaders import PyMuPDFLoader
import tiktoken
from html import escape

class RetrievalAugmentedChat:
    def __init__(self, pdf_document_path, basic_model="gpt-3.5-turbo", basic_embedding_model="text-embedding-3-small"):
        self.load_env()
        self.setup_logging()
        self.basic_model = basic_model
        self.basic_embedding_model = basic_embedding_model
        self.pdf_doc = pdf_document_path
        self.enc = tiktoken.encoding_for_model(basic_model)
        self.embedding_model = OpenAIEmbeddings(model=basic_embedding_model)
        self.chat_model = ChatOpenAI(model=self.basic_model)

    def load_env(self):
        load_dotenv()

    def setup_logging(self):
        level = logging.INFO
        logging.basicConfig(stream=sys.stdout, level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

    def load_doc_to_vectorstore(self):
        """Loads document and initializes vector store for retrieval."""
        logging.debug("Loading documents...")
        docs = PyMuPDFLoader(self.pdf_doc).load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=lambda text: len(tiktoken.encoding_for_model(self.basic_model).encode(text))
        )
        split_chunks = text_splitter.split_documents(docs)
        self.qdrant_vectorstore = Qdrant.from_documents(
            split_chunks,
            self.embedding_model,
            location=":memory:",
            collection_name="Meta10k"
        )
        self.qdrant_retriever = self.qdrant_vectorstore.as_retriever()
        logging.debug("Documents loaded and qdrant_retriever initialized.")
    
    @staticmethod
    def process_complete_context(document, word_limit=250):
        # Convert the Document object back to a dictionary
        doc_dict = document.dict()

        # Access the pageContent and metadata directly from the dictionary
        page_content = doc_dict.get('page_content', '')
        metadata = doc_dict.get('metadata', {})

        # If pageContent is empty, provide a default message
        if not page_content:
            return "No page content found in the document."

        # Clean and limit the page content
        text = escape(page_content).replace('\n', ' ')
        words = text.split()
        text = ' '.join(words[:word_limit]) + '...' if len(words) > word_limit else text

        # Extract relevant metadata information
        page = metadata.get('page', 'N/A')
        file_path = metadata.get('file_path', 'unknown file')
        
        return f"On page {page} from {file_path}, I found {text}"

    def query_and_return_answers(self, question):
        """Queries the model and retrieves answers based on provided question."""
        rag_prompt = ChatPromptTemplate.from_template("""
        CONTEXT:
        {context}

        QUERY:
        {question}

        Be as specific as possible, within the context. You should use only the context provided by the user to answer the question. Do not use other information from outside the context. If you do not know, just answer 'I don't know.'
        """)
        retrieval_augmented_qa_chain = (
            {"context": itemgetter("question") | self.qdrant_retriever, "question": itemgetter("question")}
            | RunnablePassthrough.assign(context=itemgetter("context"))
            | {"response": rag_prompt | self.chat_model, "context": itemgetter("context")}
        )
        response = retrieval_augmented_qa_chain.invoke({"question": question})
        response_content = response["response"].content

        if isinstance(response["context"], list):
            formatted_contexts = '\n\n'.join([RetrievalAugmentedChat.process_complete_context(ctx) for ctx in response["context"]])
        else:
            formatted_contexts = RetrievalAugmentedChat.process_complete_context(response["context"])

        combined_response = f"\nResponse:\n{response_content}\n----\nContext:\n{formatted_contexts}"
        return combined_response

if __name__ == "__main__":
    user_question_1 = "What was the total value of 'Cash and cash equivalents' as of December 31, 2023?"
    user_question_2 = "Who are Meta's 'Directors' (i.e., members of the Board of Directors)?"
    
    # pdf_document_path = "DataRepository/meta10k.pdf"
    pdf_document_path = 'https://d18rn0p25nwr6d.cloudfront.net/CIK-0001326801/c7318154-f6ae-4866-89fa-f0c589f2ee3d.pdf'
    basic_model = "gpt-3.5-turbo"
    basic_embedding_model = "text-embedding-3-small"
    
    chat = RetrievalAugmentedChat(pdf_document_path, basic_model, basic_embedding_model)
    chat.load_doc_to_vectorstore()

    response = chat.query_and_return_answers(user_question_1)
    print(response)