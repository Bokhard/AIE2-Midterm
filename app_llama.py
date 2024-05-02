from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.readers.file import MarkdownReader
import llama_index
from llama_index.core import set_global_handler
from llama_index.core import Settings
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.extractors import TitleExtractor
from dotenv import load_dotenv
import os
import logging
import sys

### USES LLAMAINDEX RAG PIPELINE ###


level=logging.INFO
logging.basicConfig(stream=sys.stdout, level=level, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

"""dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)
os.environ["WANDB_API_KEY"] = os.getenv("WANDB_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")"""

load_dotenv()

set_global_handler("wandb", run_args={"project": "aie2-midterm"})
wandb_callback = llama_index.core.global_handler


Settings.llm = OpenAI(temperature=0.2, model="gpt-3.5-turbo")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Temporary to test.
markdown_file = 'DataRepository/meta10k_20240501_140240.md'

financial_docs = MarkdownReader().load_data(file=markdown_file,)
logging.info('Loaded markdown file %s into financial_docs.', markdown_file)

financial_list = []
name_part = os.path.basename(markdown_file).split('_')[0]
financial_list.append(name_part)

client = QdrantClient(location=":memory:")

vector_size = 1536

client.create_collection(
    collection_name="financial_statements",
    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
)
logging.info('Created Qdrant collection with vector size of %s.', vector_size)

# Create `VectorStore` and `StorageContext` which will allow us to create an empty `VectorStoreIndex` which we will be able to add nodes to later!

vector_store = QdrantVectorStore(client=client, collection_name="financial_reports")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    [],
    storage_context=storage_context,
)
logging.info('Created Qdrant vector store index.')

# loop through our documents and metadata and construct nodes. Manually insert metadata... Meta and fiscal year, for now.

pipeline = IngestionPipeline(transformations=[TokenTextSplitter()])

for statement, doc in zip(financial_list, financial_docs):
    nodes = pipeline.run(documents=[doc])
    for node in nodes:
        node.metadata = {"Company" : "Meta", "fiscal_year" : 2023}
    index.insert_nodes(nodes)
    logging.info('Added one doc via Pipeline ingestion.')


"""
### Persisting and Loading Stored Index with Weights and Biases
# Now we can utilize a powerful feature of Weights and Biases - index and artifact versioning!
# We can persist our index to WandB to be used and loaded later!


wandb_callback.persist_index(index, index_name="financial-reports-qdrant")

from llama_index.core import load_index_from_storage
storage_context = wandb_callback.load_storage_context(
    artifact_url="bokhard85/llama-index-rag/movie-index-qdrant:v0"
)
"""

simple_rag_engine = index.as_query_engine(streaming=True)

"""for k, v in simple_rag.get_prompts().items():
  print(v.get_template())
  print("\n~~~~~~~~~~~~~~~~~~\n")"""

response = simple_rag_engine.query("What was the total value of 'Cash and cash equivalents' as of December 31, 2023?") 
response.print_response_stream()



def simple_engine():
    meta10k = SimpleDirectoryReader(
        input_files=["DataRepository/meta10k.pdf"]
    ).load_data()

    # create an index from the parsed markdown
    meta10k_index = VectorStoreIndex.from_documents(meta10k)

    # create a query engine for the index
    meta10k_engine = meta10k_index.as_query_engine()

    # query the engine
    query = "What was the total value of 'Cash and cash equivalents' as of December 31, 2023?"
    response = meta10k_engine.query(query)
    print(query)
    print(response)
    print('/n')

    # query the engine
    query = "Who are Meta's 'Directors' (i.e., members of the Board of Directors)?"
    response = meta10k_engine.query(query)
    print(query)
    print(response)
    print('/n')