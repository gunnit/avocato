Tools
Understanding and leveraging tools within the CrewAI framework for agent collaboration and task execution.

​
Introduction
CrewAI tools empower agents with capabilities ranging from web searching and data analysis to collaboration and delegating tasks among coworkers. This documentation outlines how to create, integrate, and leverage these tools within the CrewAI framework, including a new focus on collaboration tools.

​
What is a Tool?
A tool in CrewAI is a skill or function that agents can utilize to perform various actions. This includes tools from the CrewAI Toolkit and LangChain Tools, enabling everything from simple searches to complex interactions and effective teamwork among agents.

​
Key Characteristics of Tools
Utility: Crafted for tasks such as web searching, data analysis, content generation, and agent collaboration.
Integration: Boosts agent capabilities by seamlessly integrating tools into their workflow.
Customizability: Provides the flexibility to develop custom tools or utilize existing ones, catering to the specific needs of agents.
Error Handling: Incorporates robust error handling mechanisms to ensure smooth operation.
Caching Mechanism: Features intelligent caching to optimize performance and reduce redundant operations.
​
Using CrewAI Tools
To enhance your agents’ capabilities with crewAI tools, begin by installing our extra tools package:


pip install 'crewai[tools]'
Here’s an example demonstrating their use:

Code

import os
from crewai import Agent, Task, Crew
# Importing crewAI tools
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    SerperDevTool,
    WebsiteSearchTool
)

# Set up API keys
os.environ["SERPER_API_KEY"] = "Your Key" # serper.dev API key
os.environ["OPENAI_API_KEY"] = "Your Key"

# Instantiate tools
docs_tool = DirectoryReadTool(directory='./blog-posts')
file_tool = FileReadTool()
search_tool = SerperDevTool()
web_rag_tool = WebsiteSearchTool()

# Create agents
researcher = Agent(
    role='Market Research Analyst',
    goal='Provide up-to-date market analysis of the AI industry',
    backstory='An expert analyst with a keen eye for market trends.',
    tools=[search_tool, web_rag_tool],
    verbose=True
)

writer = Agent(
    role='Content Writer',
    goal='Craft engaging blog posts about the AI industry',
    backstory='A skilled writer with a passion for technology.',
    tools=[docs_tool, file_tool],
    verbose=True
)

# Define tasks
research = Task(
    description='Research the latest trends in the AI industry and provide a summary.',
    expected_output='A summary of the top 3 trending developments in the AI industry with a unique perspective on their significance.',
    agent=researcher
)

write = Task(
    description='Write an engaging blog post about the AI industry, based on the research analyst’s summary. Draw inspiration from the latest blog posts in the directory.',
    expected_output='A 4-paragraph blog post formatted in markdown with engaging, informative, and accessible content, avoiding complex jargon.',
    agent=writer,
    output_file='blog-posts/new_post.md'  # The final blog post will be saved here
)

# Assemble a crew with planning enabled
crew = Crew(
    agents=[researcher, writer],
    tasks=[research, write],
    verbose=True,
    planning=True,  # Enable planning feature
)

# Execute tasks
crew.kickoff()
​
Available CrewAI Tools
Error Handling: All tools are built with error handling capabilities, allowing agents to gracefully manage exceptions and continue their tasks.
Caching Mechanism: All tools support caching, enabling agents to efficiently reuse previously obtained results, reducing the load on external resources and speeding up the execution time. You can also define finer control over the caching mechanism using the cache_function attribute on the tool.
Here is a list of the available tools and their descriptions:

Tool	Description
BrowserbaseLoadTool	A tool for interacting with and extracting data from web browsers.
CodeDocsSearchTool	A RAG tool optimized for searching through code documentation and related technical documents.
CodeInterpreterTool	A tool for interpreting python code.
ComposioTool	Enables use of Composio tools.
CSVSearchTool	A RAG tool designed for searching within CSV files, tailored to handle structured data.
DALL-E Tool	A tool for generating images using the DALL-E API.
DirectorySearchTool	A RAG tool for searching within directories, useful for navigating through file systems.
DOCXSearchTool	A RAG tool aimed at searching within DOCX documents, ideal for processing Word files.
DirectoryReadTool	Facilitates reading and processing of directory structures and their contents.
EXASearchTool	A tool designed for performing exhaustive searches across various data sources.
FileReadTool	Enables reading and extracting data from files, supporting various file formats.
FirecrawlSearchTool	A tool to search webpages using Firecrawl and return the results.
FirecrawlCrawlWebsiteTool	A tool for crawling webpages using Firecrawl.
FirecrawlScrapeWebsiteTool	A tool for scraping webpages URL using Firecrawl and returning its contents.
GithubSearchTool	A RAG tool for searching within GitHub repositories, useful for code and documentation search.
SerperDevTool	A specialized tool for development purposes, with specific functionalities under development.
TXTSearchTool	A RAG tool focused on searching within text (.txt) files, suitable for unstructured data.
JSONSearchTool	A RAG tool designed for searching within JSON files, catering to structured data handling.
LlamaIndexTool	Enables the use of LlamaIndex tools.
MDXSearchTool	A RAG tool tailored for searching within Markdown (MDX) files, useful for documentation.
PDFSearchTool	A RAG tool aimed at searching within PDF documents, ideal for processing scanned documents.
PGSearchTool	A RAG tool optimized for searching within PostgreSQL databases, suitable for database queries.
Vision Tool	A tool for generating images using the DALL-E API.
RagTool	A general-purpose RAG tool capable of handling various data sources and types.
ScrapeElementFromWebsiteTool	Enables scraping specific elements from websites, useful for targeted data extraction.
ScrapeWebsiteTool	Facilitates scraping entire websites, ideal for comprehensive data collection.
WebsiteSearchTool	A RAG tool for searching website content, optimized for web data extraction.
XMLSearchTool	A RAG tool designed for searching within XML files, suitable for structured data formats.
YoutubeChannelSearchTool	A RAG tool for searching within YouTube channels, useful for video content analysis.
YoutubeVideoSearchTool	A RAG tool aimed at searching within YouTube videos, ideal for video data extraction.
​
Creating your own Tools
Developers can craft custom tools tailored for their agent’s needs or utilize pre-built options.

There are two main ways for one to create a CrewAI tool:

​
Subclassing BaseTool
Code

from crewai.tools import BaseTool


class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = "Clear description for what this tool is useful for, your agent will need this information to use it."

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "Result from custom tool"
​
Utilizing the tool Decorator
Code

from crewai.tools import tool
@tool("Name of my tool")
def my_tool(question: str) -> str:
    """Clear description for what this tool is useful for, your agent will need this information to use it."""
    # Function logic here
    return "Result from your custom tool"
​
Structured Tools
The StructuredTool class wraps functions as tools, providing flexibility and validation while reducing boilerplate. It supports custom schemas and dynamic logic for seamless integration of complex functionalities.

​
Example:
Using StructuredTool.from_function, you can wrap a function that interacts with an external API or system, providing a structured interface. This enables robust validation and consistent execution, making it easier to integrate complex functionalities into your applications as demonstrated in the following example:


from crewai.tools.structured_tool import CrewStructuredTool
from pydantic import BaseModel

# Define the schema for the tool's input using Pydantic
class APICallInput(BaseModel):
    endpoint: str
    parameters: dict

# Wrapper function to execute the API call
def tool_wrapper(*args, **kwargs):
    # Here, you would typically call the API using the parameters
    # For demonstration, we'll return a placeholder string
    return f"Call the API at {kwargs['endpoint']} with parameters {kwargs['parameters']}"

# Create and return the structured tool
def create_structured_tool():
    return CrewStructuredTool.from_function(
        name='Wrapper API',
        description="A tool to wrap API calls with structured input.",
        args_schema=APICallInput,
        func=tool_wrapper,
    )

# Example usage
structured_tool = create_structured_tool()

# Execute the tool with structured input
result = structured_tool._run(**{
    "endpoint": "https://example.com/api",
    "parameters": {"key1": "value1", "key2": "value2"}
})
print(result)  # Output: Call the API at https://example.com/api with parameters {'key1': 'value1', 'key2': 'value2'}
​
Custom Caching Mechanism
Tools can optionally implement a cache_function to fine-tune caching behavior. This function determines when to cache results based on specific conditions, offering granular control over caching logic.

Code

from crewai.tools import tool

@tool
def multiplication_tool(first_number: int, second_number: int) -> str:
    """Useful for when you need to multiply two numbers together."""
    return first_number * second_number

def cache_func(args, result):
    # In this case, we only cache the result if it's a multiple of 2
    cache = result % 2 == 0
    return cache

multiplication_tool.cache_function = cache_func

writer1 = Agent(
        role="Writer",
        goal="You write lessons of math for kids.",
        backstory="You're an expert in writing and you love to teach kids but you know nothing of math.",
        tools=[multiplication_tool],
        allow_delegation=False,
    )
    #...
​
Conclusion
Tools are pivotal in extending the capabilities of CrewAI agents, enabling them to undertake a broad spectrum of tasks and collaborate effectively. When building solutions with CrewAI, leverage both custom and existing tools to empower your agents and enhance the AI ecosystem. Consider utilizing error handling, caching mechanisms, and the flexibility of tool arguments to optimize your agents’ performance and capabilities.


Browserbase Web Loader
Browserbase is a developer platform to reliably run, manage, and monitor headless browsers.

​
BrowserbaseLoadTool
​
Description
Browserbase is a developer platform to reliably run, manage, and monitor headless browsers.

Power your AI data retrievals with:

Serverless Infrastructure providing reliable browsers to extract data from complex UIs
Stealth Mode with included fingerprinting tactics and automatic captcha solving
Session Debugger to inspect your Browser Session with networks timeline and logs
Live Debug to quickly debug your automation
​
Installation
Get an API key and Project ID from browserbase.com and set it in environment variables (BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID).
Install the Browserbase SDK along with crewai[tools] package:

pip install browserbase 'crewai[tools]'
​
Example
Utilize the BrowserbaseLoadTool as follows to allow your agent to load websites:

Code

from crewai_tools import BrowserbaseLoadTool

# Initialize the tool with the Browserbase API key and Project ID
tool = BrowserbaseLoadTool()
​
Arguments
The following parameters can be used to customize the BrowserbaseLoadTool’s behavior:

Argument	Type	Description
api_key	string	Optional. Browserbase API key. Default is BROWSERBASE_API_KEY env variable.
project_id	string	Optional. Browserbase Project ID. Default is BROWSERBASE_PROJECT_ID env variable.
text_content	bool	Optional. Retrieve only text content. Default is False.
session_id	string	Optional. Provide an existing Session ID.
proxy	bool	Optional. Enable/Disable Proxies. Default is False.

Firecrawl Scrape Website
The FirecrawlScrapeWebsiteTool is designed to scrape websites and convert them into clean markdown or structured data.

​
FirecrawlScrapeWebsiteTool
​
Description
Firecrawl is a platform for crawling and convert any website into clean markdown or structured data.

​
Installation
Get an API key from firecrawl.dev and set it in environment variables (FIRECRAWL_API_KEY).
Install the Firecrawl SDK along with crewai[tools] package:

pip install firecrawl-py 'crewai[tools]'
​
Example
Utilize the FirecrawlScrapeWebsiteTool as follows to allow your agent to load websites:

Code

from crewai_tools import FirecrawlScrapeWebsiteTool

tool = FirecrawlScrapeWebsiteTool(url='firecrawl.dev')
​
Arguments
api_key: Optional. Specifies Firecrawl API key. Defaults is the FIRECRAWL_API_KEY environment variable.
url: The URL to scrape.
page_options: Optional.
onlyMainContent: Optional. Only return the main content of the page excluding headers, navs, footers, etc.
includeHtml: Optional. Include the raw HTML content of the page. Will output a html key in the response.
extractor_options: Optional. Options for LLM-based extraction of structured information from the page content
mode: The extraction mode to use, currently supports ‘llm-extraction’
extractionPrompt: Optional. A prompt describing what information to extract from the page
extractionSchema: Optional. The schema for the data to be extracted
timeout: Optional. Timeout in milliseconds for the request
Was this page helpful?


Scrape Website
The ScrapeWebsiteTool is designed to extract and read the content of a specified website.

​
ScrapeWebsiteTool
We are still working on improving tools, so there might be unexpected behavior or changes in the future.

​
Description
A tool designed to extract and read the content of a specified website. It is capable of handling various types of web pages by making HTTP requests and parsing the received HTML content. This tool can be particularly useful for web scraping tasks, data collection, or extracting specific information from websites.

​
Installation
Install the crewai_tools package


pip install 'crewai[tools]'
​
Example

from crewai_tools import ScrapeWebsiteTool

# To enable scrapping any website it finds during it's execution
tool = ScrapeWebsiteTool()

# Initialize the tool with the website URL, 
# so the agent can only scrap the content of the specified website
tool = ScrapeWebsiteTool(website_url='https://www.example.com')

# Extract the text from the site
text = tool.run()
print(text)
​
Arguments
Argument	Type	Description
website_url	string	Mandatory website URL to read the file. This is the primary input for the tool, specifying which website’s content should be scraped and read.

recrawl Search
The FirecrawlSearchTool is designed to search websites and convert them into clean markdown or structured data.

​
FirecrawlSearchTool
​
Description
Firecrawl is a platform for crawling and convert any website into clean markdown or structured data.

​
Installation
Get an API key from firecrawl.dev and set it in environment variables (FIRECRAWL_API_KEY).
Install the Firecrawl SDK along with crewai[tools] package:

pip install firecrawl-py 'crewai[tools]'
​
Example
Utilize the FirecrawlSearchTool as follows to allow your agent to load websites:

Code

from crewai_tools import FirecrawlSearchTool

tool = FirecrawlSearchTool(query='what is firecrawl?')
​
Arguments
api_key: Optional. Specifies Firecrawl API key. Defaults is the FIRECRAWL_API_KEY environment variable.
query: The search query string to be used for searching.
page_options: Optional. Options for result formatting.
onlyMainContent: Optional. Only return the main content of the page excluding headers, navs, footers, etc.
includeHtml: Optional. Include the raw HTML content of the page. Will output a html key in the response.
fetchPageContent: Optional. Fetch the full content of the page.
search_options: Optional. Options for controlling the crawling behavior.
limit: Optional. Maximum number of pages to crawl.

Firecrawl Crawl Website
The FirecrawlCrawlWebsiteTool is designed to crawl and convert websites into clean markdown or structured data.

​
FirecrawlCrawlWebsiteTool
​
Description
Firecrawl is a platform for crawling and convert any website into clean markdown or structured data.

​
Installation
Get an API key from firecrawl.dev and set it in environment variables (FIRECRAWL_API_KEY).
Install the Firecrawl SDK along with crewai[tools] package:

pip install firecrawl-py 'crewai[tools]'
​
Example
Utilize the FirecrawlScrapeFromWebsiteTool as follows to allow your agent to load websites:

Code

from crewai_tools import FirecrawlCrawlWebsiteTool

tool = FirecrawlCrawlWebsiteTool(url='firecrawl.dev')
​
Arguments
api_key: Optional. Specifies Firecrawl API key. Defaults is the FIRECRAWL_API_KEY environment variable.
url: The base URL to start crawling from.
page_options: Optional.
onlyMainContent: Optional. Only return the main content of the page excluding headers, navs, footers, etc.
includeHtml: Optional. Include the raw HTML content of the page. Will output a html key in the response.
crawler_options: Optional. Options for controlling the crawling behavior.
includes: Optional. URL patterns to include in the crawl.
exclude: Optional. URL patterns to exclude from the crawl.
generateImgAltText: Optional. Generate alt text for images using LLMs (requires a paid plan).
returnOnlyUrls: Optional. If true, returns only the URLs as a list in the crawl status. Note: the response will be a list of URLs inside the data, not a list of documents.
maxDepth: Optional. Maximum depth to crawl. Depth 1 is the base URL, depth 2 includes the base URL and its direct children, and so on.
mode: Optional. The crawling mode to use. Fast mode crawls 4x faster on websites without a sitemap but may not be as accurate and shouldn’t be used on heavily JavaScript-rendered websites.
limit: Optional. Maximum number of pages to crawl.
timeout: Optional. Timeout in milliseconds for the crawling operation.

Website RAG Search
The WebsiteSearchTool is designed to perform a RAG (Retrieval-Augmented Generation) search within the content of a website.

​
WebsiteSearchTool
The WebsiteSearchTool is currently in an experimental phase. We are actively working on incorporating this tool into our suite of offerings and will update the documentation accordingly.

​
Description
The WebsiteSearchTool is designed as a concept for conducting semantic searches within the content of websites. It aims to leverage advanced machine learning models like Retrieval-Augmented Generation (RAG) to navigate and extract information from specified URLs efficiently. This tool intends to offer flexibility, allowing users to perform searches across any website or focus on specific websites of interest. Please note, the current implementation details of the WebsiteSearchTool are under development, and its functionalities as described may not yet be accessible.

​
Installation
To prepare your environment for when the WebsiteSearchTool becomes available, you can install the foundational package with:


pip install 'crewai[tools]'
This command installs the necessary dependencies to ensure that once the tool is fully integrated, users can start using it immediately.

​
Example Usage
Below are examples of how the WebsiteSearchTool could be utilized in different scenarios. Please note, these examples are illustrative and represent planned functionality:

Code

from crewai_tools import WebsiteSearchTool

# Example of initiating tool that agents can use 
# to search across any discovered websites
tool = WebsiteSearchTool()

# Example of limiting the search to the content of a specific website, 
# so now agents can only search within that website
tool = WebsiteSearchTool(website='https://example.com')
​
Arguments
website: An optional argument intended to specify the website URL for focused searches. This argument is designed to enhance the tool’s flexibility by allowing targeted searches when necessary.
​
Customization Options
By default, the tool uses OpenAI for both embeddings and summarization. To customize the model, you can use a config dictionary as follows:

Code

tool = WebsiteSearchTool(
    config=dict(
        llm=dict(
            provider="ollama", # or google, openai, anthropic, llama2, ...
            config=dict(
                model="llama2",
                # temperature=0.5,
                # top_p=1,
                # stream=true,
            ),
        ),
        embedder=dict(
            provider="google", # or openai, ollama, ...
            config=dict(
                model="models/embedding-001",
                task_type="retrieval_document",
                # title="Embeddings",
            ),
        ),
    )
)