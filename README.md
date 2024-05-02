# AIE2-Midterm
AI Makerspace Midterm Project



# Finance Getter

### SEC EDGAR Filings Query API
The Query API allows you to search and filter all 18 million filings and exhibits published on SEC EDGAR using a large set of search parameters. You can search by ticker, CIK, form type, filing date, SIC code, period of report, series and class IDs, items of 8-K and other filings, and many more. The API returns all filing metadata in a standardized JSON format. Filings are indexed and searchable as soon as they are published on SEC EDGAR.

#### The example below retrieves all 10-Q filings filed by TSLA in 2020.
```python
from sec_api import QueryApi
queryApi = QueryApi(api_key="YOUR_API_KEY")
query = {
  "query": "ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:\"10-Q\"",
  "from": "0",
  "size": "10",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = queryApi.get_filings(query)
print(filings)
```

#### Fetch most recent 8-Ks with Item 9.01 "Financial Statements and Exhibits".

```python
query = {
  "query": "formType:\"8-K\" AND items:\"9.01\"",
  "from": "0",
  "size": "10",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = queryApi.get_filings(query)
```

#### Response Format for Query API
The server returns a JSON object with two keys:

- total (object) - An object with two variables "value" and "relation". If "relation" equals "gte" (= greater than or equal), the "value" is always 10,000. This indicates that more than 10,000 filings match the query. In order to retrieve all filings, you have to iterate over the results using the "from" and "size" variables sent to the API. If "relation" equals "eq" (= equal), the "value" represents the exact number of filings matching the query. In this case, "value" is always less than 10,000. We don't calculate the exact number of matching filings for results greater than 10,000.
- filings (array) - The array holding all filings matching your filter criteria. Filing format:
    - accessionNo (string) - Accession number of filing, e.g. 0000028917-20-000033.
    - cik (string) - CIK of the filing issuer. Important: trailing 0 are removed.
    - ticker (string) - Ticker of company, e.g. AMOT. A ticker is not available when non-publicly traded companies report filings (e.g. form 4 reported by directors).
    - companyName (string) - Name of company, e.g. Allied Motion Technologies Inc
    - companyNameLong (string) - Long version of company name including the filer type (Issuer, Filer, Reporting), e.g. ALLIED MOTION TECHNOLOGIES INC (0000046129) (Issuer)
    - formType (string) - sec.gov form type, e.g 10-K. We support all 150+ form types including SEC correspondences. See the complete list of form types here.
    - description (string) - Description of the form, e.g. "Statement of changes in beneficial ownership of securities". Includes the item numbers reported in 8-K, 8-K/A, D, D/A, ABS-15G, ABS-15G/A, 1-U and 1-U/A filings, e.g. "Form 8-K - Current report - Item 1.03 Item 3.03 Item 5.02 Item 9.01".
    - linkToFilingDetails (string) - Link to HTML, XML or PDF version of the filing.
    - linkToTxt (string) - Link to the plain text version of the filing. This file can be multiple MBs large.
    - linkToHtml (string) - Link to the index page of the filing listing all exhibits and the original HTML file.
    - linkToXbrl (string, optional) - Link to XBRL version of the filing (if available). See the dataFiles array for a complete list of all XBRL files attached to the filing.
    - filedAt (string) - Represents the Accepted attribute in a filing and shows the date and time. A filing also contains a Filing Date attribute that only shows the date. The Accepted andFiling Date attribute do not have to represent the the same date. Format: YYYY-MM-DD HH:mm:SS TZ), eg 2019-12-06T14:41:26-05:00.
    - periodOfReport (string, if reported) - Period of report, e.g. 2021-06-08
    - effectivenessDate (string, if reported) - Effectiveness date, e.g. 2021-06-08
    - registrationForm (string, if reported) - Registration form as reported on EFFECT forms, e.g. S-1
    - referenceAccessionNo (string, if reported) - Reference accession number as reported on EFFECT forms, e.g. 0001213900-22-001446
    - items (array of strings, if reported) - Items represents an array of item strings as reported on form 8-K, 8-K/A, D, D/A, ABS-15G, ABS-15G/A, 1-U, 1-U/A. For example: ["Item 3.02: Unregistered Sales of Equity Securities", "Item 9.01: Financial Statements and Exhibits"]
    - groupMembers (array, if reported) - Group members represents an array of member strings as reported on SC 13G, SC 13G/A, SC 13D, SC 13D/A filings, e.g. [ "ALEC N. LITOWITZMAGNETAR CAPITAL PARTNERS LPSUPERNOVA MANAGEMENT LLC" ]
    - id (string) - Unique ID of the filing.
    - entities (array) - A list of all entities referred to in the filing. The first item in the array always represents the filing issuer. Each array element is an object with the following keys:
        - companyName (string) - Company name of the entity, e.g. DILLARD'S, INC. (Issuer)
        - cik (string) - CIK of the entity. Trailing 0 are not removed here, e.g. 0000028917
        - irsNo (string, optional) - IRS number of the entity, e.g. 710388071
        - stateOfIncorporation (string, optional) - State of incorporation of entity, e.g. AR
        - fiscalYearEnd (string, optional) - Fiscal year end of the entity, e.g. 0201
        - sic (string, optional) - SIC of the entity, e.g. 5311 Retail-Department Stores
        - type (string, optional) - Type of the filing being filed. Same as formType, e.g. 4
        - act (string, optional) - The SEC act pursuant to which the filing was filed, e.g. 34
        - fileNo (string, optional) - Filer number of the entity, e.g. 001-06140
        - filmNo (string, optional) - Film number of the entity, e.g. 20575664
    - documentFormatFiles (array) - An array listing all primary files of the filing. The first item of the array is always the filing itself. The last item of the array is always the TXT version of the filing. All other items can represent exhibits, press releases, PDF documents, presentations, graphics, XML files, and more. An array item is represented as follows:
        - sequence (string, optional) - The sequence number of the filing, e.g. 1
        - description (string, optional) - Description of the file, e.g. EXHIBIT 31.1
        - documentUrl (string) - URL to the file on SEC.gov
        - type (string, optional) - Type of the file, e.g. EX-32.1, GRAPHIC or 10-Q
        - size (string, optional) - Size of the file, e.g. 6627216
    - dataFiles (array) - List of data files (filing attachments, exhibits, XBRL files) attached to the filing.
        - sequence (string) - Sequence number of the file, e.g. 6
        - description (string) - Description of the file, e.g. XBRL INSTANCE DOCUMENT
        - documentUrl (string) - URL to the file on SEC.gov
        - type (string, optional) - Type of the file, e.g. EX-101.INS, EX-101.DEF or EX-101.PRE
        - size (string, optional) - Size of the file, e.g. 6627216
    - seriesAndClassesContractsInformation (array) - List of series and classes/contracts information.
        - series (string) - Series ID, e.g. S000001297
        - name (string) - Name of entity, e.g. PRUDENTIAL ANNUITIES LIFE ASSUR CORP VAR ACCT B CL 1 SUB ACCTS
        - classesContracts (array) - List of classes/contracts. Each list item has the following keys:
            - classContract (string) - Class/Contract ID, e.g. C000011787
            - name (string) - Name of class/contract entity, e.g. Class L
            - ticker (string) - Ticker class/contract entity, e.g. URTLX


### Filing Render & Download API
Used to download any filing or exhibit. You can process the downloaded filing in memory or save the filing to your hard drive.

```python
from sec_api import RenderApi
renderApi = RenderApi(api_key="YOUR_API_KEY")
url = "https://www.sec.gov/Archives/edgar/data/1662684/000110465921082303/tm2119986d1_8k.htm"
filing = renderApi.get_filing(url)
print(filing)
```

# Finance Parser
