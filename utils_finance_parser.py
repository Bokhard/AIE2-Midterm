import logging
from dotenv import load_dotenv
import os
import re
from datetime import datetime
from getpass import getpass
import nest_asyncio
from llama_parse import LlamaParse
import PyPDF2

def setup_logging(level=logging.INFO):
    """
    Setup basic configuration for logging.
    """
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

class SECFilingsParser:
# pip install -U llama-index --upgrade --no-cache-dir --force-reinstall
    def __init__(self, llama_api_key, input_file):
        """
        Initializes the filing parser with an API key.
        """
        self.llama_api_key = llama_api_key
        self.input_file = input_file
        self.parser = LlamaParse(
            api_key=self.llama_api_key,
            result_type="markdown",
            verbose=True
        #    parsing_instruction=parsingInstruction10k
        )

    def extract_first_x_pages(self, input_pdf_path, number_of_pages):
        """
        Extracts the first X number of pages from a PDF.
        """
        with open(input_pdf_path, "rb") as infile:
            reader = PyPDF2.PdfReader(infile)
            writer = PyPDF2.PdfWriter()
            num_pages_to_extract = min(number_of_pages, len(reader.pages))
            for i in range(num_pages_to_extract):
                writer.add_page(reader.pages[i])
            
            # Temporarily save to a buffer or file if needed
            output_pdf_path = input_pdf_path.replace('.pdf', '_head.pdf')
            with open(output_pdf_path, "wb") as outfile:
                writer.write(outfile)
            return output_pdf_path 
        
    parsingInstruction10k = """The provided document is a corporate annual report 10-K.
    It contains both textual comments and also tables of financial data.
    Do not change or add anything when parsing - try to keep it as precisely accurate to the source data.
    There is one exception: Most pages begins with 'Table of Contents' and ends with a page number and line break. If you find these, you can exclude them from the output."""

    def parse_10k(self, input_file):
        """
        Parse and clean a 10-K filing and save to markdown.
        """
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        logging.debug('Loading file: %s', base_name)
        documents = self.parser.load_data(input_file)

        if isinstance(documents, list):
            documents = '\n'.join([doc.text for doc in documents])
        
        logging.debug('Cleaning parsed documents.')
        documents = self.clean_documents(documents)
        
        datetime_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"DataRepository/{base_name}_{datetime_stamp}.md"
        with open(output_file, 'w') as file:
            file.write(documents)
            logging.info(f"Filing saved to {output_file}")
        return output_file

    def clean_documents(self, documents):
        unwanted_pattern = re.compile(r"^---+\s*\n## Table of Contents\n", re.MULTILINE)
        return re.sub(unwanted_pattern, '', documents)


if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)

    llama_api_key = os.getenv('LLAMA_API_KEY')
    if not llama_api_key:
        llama_api_key = getpass("Please provide your Llama Cloud API Key: ")
        logging.debug('API key provided via user input.')

    input_10k = 'DataRepository/meta10k.pdf'
    logging.debug('Beginning to extract the first 10 pages of the PDF file: %s', input_10k)

    # Instantiate the parser
    parser = SECFilingsParser(llama_api_key, input_10k)

    # Extract the first 10 pages and receive the new file's path
    extracted_file_path = parser.extract_first_x_pages(input_10k, 10)
    logging.debug('Extracted first 10 pages saved to: %s', extracted_file_path)

    # Now parse the extracted file
    logging.debug('Beginning to parse the extracted file: %s', extracted_file_path)
    output_markdown = parser.parse_10k(extracted_file_path)
    logging.info('Parsing completed and output saved to: %s', output_markdown)
