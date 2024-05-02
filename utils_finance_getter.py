import logging
import os
import re
from datetime import datetime
from getpass import getpass
import nest_asyncio
from llama_parse import LlamaParse
from sec_api import QueryApi, RenderApi
import PyPDF2

def setup_logging(level=logging.INFO):
    """
    Setup basic configuration for logging.
    """
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

class SECFilingsGetter:
    def __init__(self, sec_api_key):
        """
        Initializes the downloader with an API key.
        """
        self.query_api = QueryApi(api_key=sec_api_key)
        self.render_api = RenderApi(api_key=sec_api_key)

    def search_filings(self, ticker, filing_year, form_type):
        """
        Search filings using QueryApi based on ticker, year, and form type.
        """
        query = {
          "query": f"ticker:{ticker} AND filedAt:[{filing_year}-01-01 TO {filing_year}-12-31] AND formType:\"{form_type}\"",
          "from": "0",
          "size": "10",
          "sort": [{"filedAt": {"order": "desc"}}]
        }
        logging.debug('Searching filings with query: %s', query)
        try:
            filings = self.query_api.get_filings(query)
            logging.info(f"{len(filings['filings'])} filings found.")
            return filings['filings']
        except Exception as e:
            logging.error(f"Error searching filings: {e}")
            raise

    def download_filing(self, filing_data, prefer_text=False):
        """
        Download the filing content using RenderApi based on the preferred format.
        """
        filing_url = filing_data.get('linkToTxt') if prefer_text and 'linkToTxt' in filing_data else filing_data.get('linkToFilingDetails')
        logging.info(f"Downloading filing from URL: {filing_url}")
        try:
            filing_content = self.render_api.get_filing(filing_url)
            logging.info("Filing downloaded successfully.")
            return filing_content
        except Exception as e:
            logging.error(f"Failed to download the document: {e}")
            raise

    def save_filing(self, filing_content, output_path):
        """
        Save the downloaded filing content to a local file.
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(filing_content)
            logging.info(f"Filing saved to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save the filing: {e}")
            raise

if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    sec_api_key = getpass("Please provide your SEC API Key: ")
    downloader = SECFilingsGetter(sec_api_key)

    try:
        ticker = input("Enter the company ticker: ")
        filing_year = input("Enter the year of the filing: ")
        form_type = input("Enter the form type (e.g., '10-K'): ")
        user_input = input("Prefer plain text format? (yes/no): ").strip().lower()
        prefer_text = user_input[0] == 'y' if user_input else False

        
        filings = downloader.search_filings(ticker, filing_year, form_type)
        if filings:
            for filing in filings:
                filing_content = downloader.download_filing(filing, prefer_text)
                file_extension = 'txt' if prefer_text else 'html'
                datetime_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
                output_path = f"DataRepository/{ticker}_{filing_year}_{form_type}_{datetime_stamp}.{file_extension}"
                downloader.save_filing(filing_content, output_path)
        else:
            logging.info("No filings found to download.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
