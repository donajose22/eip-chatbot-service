from langchain_sdk.Langchain_sdk import LangChainCustom 
from config.config import global_config
import json

config = global_config

def generate_model(prompt = None):
    client_id = config["genai_client_id"]
    client_secret = config["genai_secret"]

    if(prompt==None):
        prompt = 'Summarize everything in 100 words.'

    llm = LangChainCustom(client_id=client_id,
                            client_secret=client_secret,
                            model="gpt-4-turbo",
                            temperature=1,
                            chat_conversation=True,
                            conversation_history = [],
                            system_prompt=prompt)                    
    return llm

def create_formatter_prompt(question, input):
    prompt = f'''
    You are tasked with converting a given text into HTML format based on the question. 

    QUESTION:
    {question}
    
    INPUT TEXT:
    {input}
    
    Please follow these guidelines:

    Do not modify any of the content. Only add the appropriate HTML tags wherever necessary.

    Do not include any <html> or <body> tags. The output should contain only the content and relevant HTML tags within the body of the page.

    If there are any SQL Queries in the text, it should be highlighted and emphasized.

    Paragraphs: Each paragraph should be separated by the <p></p> tags.

    Unordered Lists: Items in an unordered list should be denoted using the <ul> and <li> tags. Use - to mark list items in the original text and convert them to HTML list items.

    Ordered Lists: Items in an ordered list should be denoted using the <ol> and <li> tags. Convert numbered points in the text to an ordered list.

    Bold Important Words: Some words that are important or emphasized (such as terms, names, or concepts) should be enclosed in the <b></b> tags. You can infer the importance based on context. 
    Only highlight the important words once in the beginning. Emphasize at most 2 words/phrases in a sentence. Emphasize the main words that answer the question.

    Line Breaks: Use <br> where necessary for line breaks (i.e., where a paragraph should continue on a new line but does not require a full paragraph break).

    Images: If the text contains image URLs, use the <img> tag to insert the image with the src attribute. Ensure the image source URL is inserted properly, for example:
    <img src="URL_HERE" alt="Description of the image">

    Links: For any webpage URLs or references to external sources, use the <a> tag to create clickable links. The link should point to the source, and the anchor text should describe the content or provide context. The links should open in a new tab. For example:
    <a href="URL_HERE">Link Description</a>

    Headings: If the text contains headings or subheadings, use the appropriate heading tags (<h1>, <h2>, etc.) based on the hierarchy of the text. For example, major headings should use <h1>, subheadings should use <h2>, and so on.

    Additional Formatting: If there are any other formatting elements (such as italics, bold, etc.), make sure to convert them properly into HTML tags (<i></i> for italics, <b></b> for bold, etc.).

    Example Input:

    "Here is a sample paragraph. It's followed by a list of items:

    - Item one
    - Item two
    - Item three

    Also, visit this page for more information: www.example.com

    Here's an important image:
    http://example.com/sample-image.jpg"

    Expected HTML Output:

    "<p>Here is a sample paragraph. It's followed by a list of items:</p>

    <ul>
    <li>Item one</li>
    <li>Item two</li>
    <li>Item three</li>
    </ul>

    <p>Also, visit this page for more information: <a href="http://www.example.com">www.example.com</a></p>

    <p>Here's an important image:</p>
    <img src="http://example.com/sample-image.jpg" alt="Sample Image">"


    Please convert the given text according to these instructions. Do not include the <html> or <body> tags in the output. 
    If it is already in html format, don't change that portion. Only format the portion that is not already in html format.
    Only highlight the main words/phrases that answer the question. Do not highlight/bold any unnecessary words.
    Do not include any additional text or quotes in the beginning or end of the response. No quotes or backticks.
    '''

    return prompt

def format_json(text):
    text = text[2:-1]
    text = text.replace("\\'", "'").replace('\\"', '"').replace("\\\\n", "\n")
    json_data = json.loads(text, strict=False)
    return json_data

def format(question, input):
    print("****************************Formatting********************************************************")

    model = generate_model()

    input_prompt = create_formatter_prompt(question, input)

    response = model.invoke(input_prompt)

    # convert response to json format
    json_data = format_json(response)
    formatted_response = json_data["currentResponse"]

    # print(formatted_response)

    return formatted_response