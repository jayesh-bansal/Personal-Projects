# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "fastapi",
#     "uvicorn",
#     "requests",
#     "sentence_transformers",
# ]
# ///
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pathlib import Path
import os
import requests
import json
import subprocess
import glob
import sqlite3
from sentence_transformers import SentenceTransformer, util
import hashlib


app = FastAPI()

app.add_middleware (
    CORSMiddleware ,
    allow_origins = ['*'],
    allow_credentials = True,
    allow_methods = ["GET","POST"],
    allow_headers = ['*']
)


AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

url="https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    
headers={
        "Content-type":"application/json",
        "Authorization":f"Bearer {AIPROXY_TOKEN}"
    } 
    
def script_runner(script_url: str,email: str,package: str):
    import importlib.util
    package_spec = importlib.util.find_spec(package)
    if package_spec is None:
        subprocess.run(["pip","install",package])

    response1 = requests.get(script_url)
    with open("datagen.py", 'w') as file:
        file.write(response1.text)
    subprocess.run(["cmd","/c","uv",'run',script_url,email])

    return {"file has been created"}

def formatting(input_location: str, tool: str):
    subprocess.run(["npx",tool,'--write',input_location],check=True)
    return {"file has been successfully formatted"}

def count_wednesday(input_location: str,output_location:str, day: str):
    from datetime import datetime

    with open(input_location, 'r') as f:
        dates = f.readlines()
    formats = [
        "%Y-%m-%d",  # 2024-03-14
        "%d-%b-%Y",  # 14-Mar-2024
        "%b %d, %Y",  # Mar 14, 2024
        "%Y/%m/%d %H:%M:%S",  # 2024/03/14 15:30:45
    ]
    count = 0
    for date_str in dates:
        parsed_date = None
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                break
            except ValueError:
                continue
        if parsed_date and parsed_date.strftime('%A')==day:
            count += 1
    with open(output_location, 'w') as f:
        f.write(str(count))
    return {"message": "Wednesdays counted successfully."}

def sort_contacts(input_location: str,output_location: str,sort_by_1: str,sort_by_2: str):
    import pandas as pd
    contacts = pd.read_json(input_location)
    contacts.sort_values([sort_by_1,sort_by_2]).to_json(output_location,orient="records")
    return {"Successfully Sorted the Contacts at":output_location}


def recent_logs(input_location: str, output_location: str, file_type:str=".log"):
    log_files = sorted(glob.glob(f"{input_location}*{file_type}"), key=os.path.getmtime, reverse=True)[:10]
    print(log_files)
    with open(output_location, 'w') as output:
        for log_file in log_files:
            with open(log_file, 'r') as file:
                first_line = file.readline().rstrip()
                output.write(first_line)
                if log_file!=log_files[-1]:
                    output.write("\n")
    return {"message": "Recent logs processed successfully."}

def index_markdown(input_location: str, output_location: str, file_type: str, tag: str):
    index = {}
    md_files = glob.glob(f'{input_location}/**/*{file_type}', recursive=True)
    for md_file in md_files:
        with open(md_file, 'r') as file:
            for line in file:
                if line.startswith(tag):
                    filename = md_file.replace(input_location[:-1], '')
                    filename = filename.replace("\\", '/')
                    index[filename[1:]] = line[2:].strip()
                    break
    with open(output_location, 'w') as f:
        json.dump(index, f, indent=4)
    return {"message": "Markdown index created successfully."}

def extract_email(input_location: str, output_location: str):
    import re
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Extract the sender's email address from this text:"},
            {"role": "user", "content": open(input_location, 'r').read()}
        ]
    }
    response = requests.post(url=url, headers=headers, json=data)
    email = response.json()['choices'][0]['message']['content'].strip()
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email)
    email = email_match.group(0) if email_match else "No valid email found"
    with open(output_location, 'w') as f:
        f.write(email)
    return {"message": "Email extracted successfully."}

def extract_credit_card(input_location: str, output_location: str):
    import base64

    try:
        with open(input_location, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read image: {e}")
    
    prompt_text = (
        "This image contains a printed numeric sequence which is about 12 to 18 digits long"
        "Extract ONLY the numeric sequence which start at first and return it as a continuous string. "
        "Do NOT include any spaces, dashes, or words."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 50
    }

    response = requests.post(url=url, headers=headers, json=data)
    card_number = response.json()['choices'][0]['message']['content'].strip()
    with open(output_location, 'w') as f:
        f.write(card_number)
    return {"message": "Credit card number extracted successfully."}

def comment_pair(input_location: str, output_location: str):
    import numpy as np
    url="https://aiproxy.sanand.workers.dev/openai/v1/embeddings"
    def get_embedding(texts):
        # Accepts a list of strings and returns a list of embeddings
        payload = {
            "model": "text-embedding-3-small",
            "input": texts
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            # Extract all embeddings
            return np.array([item['embedding'] for item in response_data['data']])
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching embeddings: {e}")
            return None

    def cosine_similarity(embeddings):
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized_embeddings = embeddings / norm
        return np.dot(normalized_embeddings, normalized_embeddings.T)

    # Read comments from input file
    with open(input_location, "r", encoding="utf-8") as file:
        comments = [line.strip() for line in file.readlines() if line.strip()]
    
    # Fetch embeddings in one batch request
    embeddings = get_embedding(comments)
    if embeddings is None:
        return {"error": "Failed to get embeddings."}

    # Compute similarity matrix
    similarity_matrix = cosine_similarity(embeddings)

    # Find the most similar pair (excluding diagonal)
    np.fill_diagonal(similarity_matrix, -1)  # Avoid self-comparison
    max_index = np.unravel_index(np.argmax(similarity_matrix), similarity_matrix.shape)

    most_similar_pair = (comments[max_index[0]], comments[max_index[1]])

    # Write to output file
    with open(output_location, "w", encoding="utf-8") as file:
        file.write(most_similar_pair[0] + "\n")
        file.write(most_similar_pair[1])
                   
    return {"message": "Most similar comments found."}


def ticket_sales(input_location: str,output_location:str):
    conn = sqlite3.connect(input_location)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    total_sales = cursor.fetchone()[0]
    conn.close()
    with open(output_location, 'w') as f:
        f.write(str(total_sales))
    return {"message": "Total sales for Gold tickets calculated successfully."}

run_url={
        "type":"function",
        "function": {
        "name": "script_runner",
        "description": "Install a package and run a script from a url and run with the email provided with it",
        "parameters":{
            "type":"object",
            "properties":{
                "script_url":{
                    "type":"string",
                    "description":"The URL of the scipt to run."
                },
                "email":{
                    "type":"string",
                    "description":"access the script url with the email"
                },
                "package":{
                    "type":"string",
                    "description":"this is a required item/package to run the script"
                }
            },"required":["script_url","email"]
        }
        }
    }

format_file={
        "type":"function",
        "function": {
        "name": "formatting",
        "description": '''This function takes 2 arguments i.e., 1 is location and other is the tool which should be applied
        at the given location''',
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"At this location is the file which we needs to be formatted"
                },
                "tool":{
                    "type":"string",
                    "description":"This is the tool used to format the file at the given location"
                },
                
            },      
        },"required":["input_location","tool"]
    },
}

count_wednesday_={
        "type":"function",
        "function": {
        "name": "count_wednesday",
        "description": '''This function takes 3 arguments with 2 as locations and 1 as day. the data file of txt is stored in the 1st 
        location. we have to count the number of days in that file and write the result in the a new file and store it in the 
        2nd location''',
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"At this location is the json file which we need to sort"
                },
                "output_location":{
                    "type":"string",
                    "description":"We should save the sorted json file at this location"
                },
                "day":{
                    "type":"string",
                    "description":"count the day needed"
                },
            },      
        },"required":["input_location","output_location","day"]
    },
}

sort_contacts_={
        "type":"function",
        "function": {
        "name": "sort_contacts",
        "description": '''This function takes 2 locations and a data file of json is stored in the 1st location. we have to sort 
        that json file by sort_by_1 argument and then by sort_by_2 argument. After sorting it, we have to store it at the 2nd location''',
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"At this location is the json file which we need to sort"
                },
                "output_location":{
                    "type":"string",
                    "description":"We should save the sorted json file at this location"
                },
                "sort_by_1":{
                    "type":"string",
                    "description":"the key for which we need to the file to be sorted on primary"
                },
                "sort_by_2":{
                    "type":"string",
                    "description":"the key for which we need to the file to be sorted on secondary"
                },
            },      
        },"required":["input_location","output_location","sort_by_1","sort_by_2"]
    },
}

recent_logs_={
        "type":"function",
        "function": {
        "name": "recent_logs",
        "description": "This function takes 3 arguments 1 is file type and 2 are locations, input location and output location. it sorts the file at the input location with the given file type with respect to the time descending. It then creates a new file and add the first line of the top 10 files in that location and saves that file in the output location",
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"Location where the required file is located"
                },
                "output_location":{
                    "type":"string",
                    "description":"Location where the new file will be saved"
                },
                "file_type":{
                    "type":"string",
                    "description":"type of the file on which extraction sohuld be done"    
                }
            },"required":["input_location","output_location","file_type"]
        }
        }
    }

index_markdown_={
        "type":"function",
        "function": {
        "name": "index_markdown",
        "description": "This function takes 4 arguments 1 is file type, 1 is tag and 2 are locations where locations are input location and output location, tag argument will say which tag we need and file type will sat which file we need to proceed on. it first creates a dictionary with key as the location and value as the first tag value located at the input location with the file tag. It then creates a new file and add that dictionary as json in that location and saves that file in the output location",
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"Location where the required file is located"
                },
                "output_location":{
                    "type":"string",
                    "description":"Location where the new file will be saved"
                },
                "file_type":{
                    "type":"string",
                    "description":"type of the file on which extraction sohuld be done"    
                },
                "tag":{
                    "type":"string",
                    "description":"it will be the tag i.e. a line starting with given value"    
                
                }
            },"required":["input_location","output_location","file_type","tag"]
        }
        }
    }

extract_email_={
        "type":"function",
        "function": {
        "name": "extract_email",
        "description": "This function takes 2 locations i.e. input location and output location. we create a llm using the AIProxy  and then send a message to the llm asking to read the file from the input location and then extract the sender email in that. Then it creates a new file and saves the sender's email and save that file at the output location.",
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"Location of the file where we need to extract the email from that file"
                },
                "output_location":{
                    "type":"string",
                    "description":"Location where the new file will be saved containing the sender email"
                }
            },"required":["input_location","output_location"]
        }
        }
    }

extract_creditcard_={
        "type":"function",
        "function": {
        "name": "extract_credit_card",
        "description": "This function takes 2 locations i.e. input location and output location. we create a llm using the AIProxy and then send a message to the llm asking to extract a 16-digit number from the file in the input location and then extract that number in a new file and save that file at the output location.",
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"Location of the file where we need to extract the 16-digit number from that file"
                },
                "output_location":{
                    "type":"string",
                    "description":"Location where the new file will be saved containing the `6-digit` number extracted"
                }
            },"required":["input_location","output_location"]
        }
        }
    }

comment_pair_={
        "type":"function",
        "function": {
        "name": "comment_pair",
        "description": "This function takes 2 locations i.e. input location and output location. at the input location, we will find the comments and the comments are passed to the llm storing the response in a list. after that we check the list to find the most similiar pair. the most simliar pair is stored in a new file which is then saved at the output location",
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"Location of the file where we the comments are mentioned"
                },
                "output_location":{
                    "type":"string",
                    "description":"Location where the new file will be saved containing the most similar comment"
                }
            },"required":["input_location","output_location"]
        }
        }
    }

ticket_sales_={
    "type":"function",
    "function": {
        "name": "ticket_sales",
        "description": "This takes 2 arguments which are location (input location and output location). then we access the database at the input location with sql and find the sum of tickets where type is gold and keep the sum in the new file and save that file in the output location",
        "parameters":{
            "type":"object",
            "properties":{
                "input_location":{
                    "type":"string",
                    "description":"Location of the file where we the database file is available"
                },
                "output_location":{
                    "type":"string",
                    "description":"Location where the new file will be saved containing the sum of the tickets with gold type"
                }
            },"required":["input_location","output_location"]
        }
    }
}


def restrict_access_exfiltered(path: str):
    folder = Path("./data").resolve()
    path=Path(path).resolve()
    if path!=folder and folder not in path.parents:
        raise HTTPException(status_code=403, detail="Access to this folder is forbidden.")
    
    if path.is_dir():
        return {"this folder is allowed"}
    
    # If the requested path is a file, read its contents
    if path.is_file():
        try:
            # Open the file in read mode and read the content
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            return content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
    # If it's neither a file nor a folder, deny access
    raise HTTPException(status_code=404, detail="File or folder not found.")

def forbid_delete():
    raise HTTPException(status_code=403, detail="The specified file or path cannot be deleted")
    
def fetch_data(input_path:str, output_path: str):
    # with 
    pass
def clone_commit_git(url: str, path: str, commit_message: str="Comitted successfully"):
    from git import Repo
    
    repo = Repo.clone_from(url,path)
    repo.index.commit(commit_message)
    origin = repo.remote(name="origin")
    origin.push()
    return {"Successfully cloned and commited and pushed"}

def run_sql_query():
    pass

def scape_data(url: str,output_location: str):
    from bs4 import BeautifulSoup
    response = requests.get(url)

    soup = BeautifulSoup(response.content,'html.parser')

    html_content = soup.prettify()
        
        # Save the full HTML to a file
    with open(output_location, "w", encoding="utf-8") as file:
        file.write(html_content)
        
        # Extract all text
        all_text = soup.get_text(separator='\n', strip=True)
        
        # Save the text content to a file
        with open("all_text.txt", "w", encoding="utf-8") as file:
            file.write(all_text)
        
        # Extract all links
        with open("all_links.txt", "w", encoding="utf-8") as file:
            for link in soup.find_all('a', href=True):
                file.write(link['href'] + "\n")
    
        # Extract all images
        with open("all_images.txt", "w", encoding="utf-8") as file:
            for img in soup.find_all('img', src=True):
                file.write(img['src'] + "\n")

    return {"Successfully scaped the data from the link"}

def compress_resize_image(path:str, to_do: str, output_location: str=None, max_width: str=None, max_height: str=None):
    from PIL import Image

    output_location = output_location or path
    def compress(output_location,quality=80):
        img.save(output_location, optimize=True, quality=quality)
    
    def resize(max_width,max_height):
        img.thumbnail((max_height,max_width))
        
    with Image.open(path) as img:
        if "resize" in to_do:
            resize(max_width,max_height)
    with Image.open(path) as img:
        if "compress" in to_do:
            compress(output_location)
    return {f'{to_do} successfully completed'}

def mp3_to_audio():
    pass

def markdown_to_html(path: str, output_location: str):
    from markdown import markdown
    with open(path,"r",encoding="UTF-8") as f:
        content = f.read()

    content = markdown(content)

    with open(output_location,"w", encoding="utf-8") as f:
        f.write(content)
    return {"Markdown successfully converted to HTML"}


def filter_csv():
    pass


restrict_access_ = {
    "type": "function",
    "function":{
        "name":"restrict_access_exfiltered",
        "description": "check if the given folder or file is accessible or exfiltered",
        "parameters":{
            "type":"object",
            "properties":{
                "path":{
                    "type":"string",
                    "description": "check if the path is accessible or not"
                }
            },"required":["path"]
        }
    }
}

forbid_delete_ = {
    "type": "function",
    "function": {
        "name": "forbid_delete",
        "description": "Prevents deletion of any file or folder",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

fetch_data_ = {
    "type": "function",
    "function": {
        "name": "fetch_data",
        "description": "Prevents deletion of any file or folder",
        "parameters": {
            "type": "object",
            "properties": {
                "url":{
                    "type": "string",
                    "description":"this is the url of git which is required for the cloning"
                },
                "path":{
                    "type": "string",
                    "description":"this is the path where the cloned git will be stored"
                },
                "commit_message":{
                    "type": "string",
                    "description":"this is the message used when commiting the git repo"
                },
            },
            "required": ["url","path","commit_message"]
        }
    }
}


clone_commit_git_ = {
    "type": "function",
    "function": {
        "name": "clone_commit_git",
        "description": "it takes 3 arguements, 1st is for the git url which we need to clone, 2nd is the location of where to commit and 3rd is an optional argumen which can be used to commit the message needed at the time of commit. this function creates a clone and commit it with the commit message and push it a the origin",
        "parameters": {
            "type": "object",
            "properties": {
                "url":{
                    "type": "string",
                    "description":"this is the url of git which is required for the cloning"
                },
                "path":{
                    "type": "string",
                    "description":"this is the path where the cloned git will be stored"
                },
                "commit_message":{
                    "type": "string",
                    "description":"this is the message used when commiting the git repo"
                },
            },
            "required": ["url","path"]
        }
    }
}

run_query_ = {
    "type": "function",
    "function": {
        "name": "run_sql_query",
        "description": "Prevents deletion of any file or folder",
        "parameters": {
            "type": "object",
            "properties": {
            },
            "required": ["url","path","commit_message"]
        }
    }
}

scape_data_ = {
    "type": "function",
    "function": {
        "name": "scape_data",
        "description": "it takes 2 arguments. 1 argument is url which is used to scrape the data and 2nd argument will save the data inside the url to the location",
        "parameters": {
            "type": "object",
            "properties": {
                "output_location":{
                    "type":"string",
                    "description":"it is the location of the file where the scaped data will be saved"
                },
                "url": {
                    "type":"string",
                    "description":"it contains the url of the website from which we need to scrape the data"
                }
            },
        }
    }
}

compress_resize_image_ = {
    "type": "function",
    "function": {
        "name": "compress_resize_image",
        "description": "it takes 5 arguments from which 3 are optional and 2 are required. it takes the img from the path and uses the to_do argument to see if the img needs to be resized or compressed and then called to its respective function. it then saves at the output location if specified else it does an in-build replace. the optional arguments are required to know the new dimensions of the resized img, if not mentioned then it returns the original img",
        "parameters": {
            "type": "object",
            "properties": {
                "output_location":{
                    "type": "string",
                    "description":"this is the location where the new img is saved"
                },
                "path":{
                    "type": "string",
                    "description":"this is the path where the img is located"
                },
                "to_do":{
                    "type": "string",
                    "description":"this is the task required to do on the img i.e., resize or compress"
                },
                "max_width":{
                    "type": "integer",
                    "description":"it contains the integer of width for which the resize img should be convert to."
                },
                "max_height":{
                    "type": "integer",
                    "description":"it contains the integer of height for which the resize img should be convert to."
                },
            },
            "required": ["path","to_do"]
        }
    }
}

mp3_to_audio_ = {
    "type": "function",
    "function": {
        "name": "mp3_to_audio",
        "description": "Prevents deletion of any file or folder",
        "parameters": {
            "type": "object",
            "properties": {
            },
        }
    }
}

markdown_to_html_ = {
    "type": "function",
    "function": {
        "name": "markdown_to_html",
        "description": "it takes 2 arguments: path and output location. path is the location where the markdown file is there and using the function it converts it into html and save the html file at the output location.",
        "parameters": {
            "type": "object",
            "properties": {
                "output_location":{
                    "type": "string",
                    "description":"location to save the converted html file"
                },
                "path":{
                    "type": "string",
                    "description":"this is the path where the markdown file is there to convert"
                },
            },
            "required": ["output_location","path"]
        }
    }
}

filter_csv_ = {
    "type": "function",
    "function": {
        "name": "filter_csv",
        "description": "Prevents deletion of any file or folder",
        "parameters": {
            "type": "object",
            "properties": {
            },
        }
    }
}

function_mapper = {
    "script_runner": script_runner,
    "formatting": formatting,
    "sort_contacts": sort_contacts,
    "count_wednesday": count_wednesday,
    "recent_logs":recent_logs,
    "index_markdown":index_markdown,
    "extract_email":extract_email,
    "extract_credit_card":extract_credit_card,
    "comment_pair":comment_pair,
    "ticket_sales": ticket_sales,
    "restrict_access_exfiltered":restrict_access_exfiltered,
    "forbid_delete":forbid_delete,
    "fetch_data":fetch_data,
    "clone_commit_git":clone_commit_git,
    "run_sql_query":run_sql_query,
    "scape_data":scape_data,
    "compress_resize_image":compress_resize_image,
    "mp3_to_audio":mp3_to_audio,
    "markdown_to_html":markdown_to_html,
    "filter_csv":filter_csv
}
tools = [run_url,format_file,count_wednesday_,sort_contacts_,recent_logs_,index_markdown_,extract_email_,extract_creditcard_,
         comment_pair_, ticket_sales_,restrict_access_,forbid_delete_,fetch_data_,clone_commit_git_,run_query_,scape_data_,
         mp3_to_audio_,markdown_to_html_,filter_csv_,compress_resize_image_]

model = SentenceTransformer("all-MiniLM-L6-v2")

    # Define representative tasks for function calling
function_call_examples = [
    "Install uv (if required) and run https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py with ${user.email} as the only argument. (NOTE: This will generate data files required for the next tasks.)",
    "Format the contents of /data/format.md using prettier@3.4.2, updating the file in-place",
    "The file /data/dates.txt contains a list of dates, one per line. Count the number of Wednesdays in the list, and write just the number to /data/dates-wednesdays.txt",
    "Sort the array of contacts in /data/contacts.json by last_name, then first_name, and write the result to /data/contacts-sorted.json",
    "Write the first line of the 10 most recent .log file in /data/logs/ to /data/logs-recent.txt, most recent first",
    "Find all Markdown (.md) files in /data/docs/. For each file, extract the first occurrance of each H1 (i.e. a line starting with # ). Create an index file /data/docs/index.json that maps each filename (without the /data/docs/ prefix) to its title",
    "/data/email.txt contains an email message. Pass the content to an LLM with instructions to extract the sender’s email address, and write just the email address to /data/email-sender.txt",
    "/data/credit-card.png contains a credit card number. Pass the image to an LLM, have it extract the card number, and write it without spaces to /data/credit-card.txt",
    "/data/comments.txt contains a list of comments, one per line. Using embeddings, find the most similar pair of comments and write them to /data/comments-similar.txt, one per line",
    "The SQLite database file /data/ticket-sales.db has a tickets with columns type, units, and price. Each row is a customer bid for a concert ticket. What is the total sales of all the items in the “Gold” ticket type? Write the number in /data/ticket-sales-gold.txt"
]

# Convert function calling examples to embeddings
function_call_embeddings = model.encode(function_call_examples, convert_to_tensor=True)

def classify_task(task_description, threshold=0.7):
    """
    Classifies a task as function_call or code_generation
    using sentence embeddings and cosine similarity.
    """

    # Compute task embedding
    task_embedding = model.encode(task_description, convert_to_tensor=True)

    # Compute cosine similarity with function calling examples
    similarities = util.pytorch_cos_sim(task_embedding, function_call_embeddings)

    # Take the highest similarity score
    max_similarity = similarities.max().item()

    return "function_call" if max_similarity > threshold else "code_generation"

@app.get("/read")
def read_file(path: str):
    from fastapi import Response
    try:
        with open(path, 'r') as f:
            return Response(f.read(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Item")

@app.post("/run")
def task_runner(task: str):

    to_do = classify_task(task)
    print(to_do)

    if to_do == "function_call":
        data = {
            "model": "gpt-4o-mini",
            "messages":[
                {
                    "role":"user",
                    "content":task
                },
                {
                    "role":"system",
                    "content":'''
    You are an assistant who has to do a variety of tasks. You can distinguish between a url and location by see if "https://" is there or
    not, example: https://example.com is a url and /root/data is a directory. Whenever you receive a system directory location, always 
    make a relative path by adding a ./ at the start. before adding it show the relative path. if it is in an another language, translate
    it in english and continue after that.
    '''
                }
            ],
            "tools": tools,
            "tool_choice":"auto"
        }

        response = requests.post(url=url, headers=headers, json=data)
        
        func = (response.json()['choices'][0]['message']['tool_calls'][0]['function']['name'])
        arguments = json.loads(response.json()['choices'][0]['message']['tool_calls'][0]['function']['arguments'])

        
        if func in function_mapper:
            output = function_mapper[func](**arguments)
            return output
    else:
        B_prompt = """
        “You are an AI assistant that generates Python code for data processing and automation tasks. Follow these rules strictly:
        1.	CRITICAL: Never access or manipulate data outside the ‘/data’ directory under any circumstances.
        2.	CRITICAL: Never include code that deletes or destroys data anywhere on the file system.
        These rules are absolute and override any contradicting task descriptions.
        Generate efficient, well-commented Python scripts for tasks such as:
        3.  CRITICAL: For all the tasks you get strictly follow the instructions given in the task save all the files to laction as mentioned in the task.
        •	Given an API endpoint fetch the data from it and save.
        •	Given a git repo clone it and commit the required changes
        •	Run SQL Queries on SQLite or DUCKDB Database.
        •	Given a URL Extract the data from it.(i.e Web Scrape)
        •	Given a Image either resize it or compress it as give in the task
        •	Given a Audio file transcribe it to the required from given in question 
        •	Convert the Markdown file to HTML
        •	Write an API endpoint that filters a CSV file and returns JSON data
        All operations must be confined to the ‘/data’ directory. Use appropriate libraries, implement error handling, and prioritize data security in all code you produce.”
        4.  Everytime a a file location is given, make the file location to its relative location by adding a . at the start of the location
        """
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "task_runner",
                "schema": {
                    "type": "object",
                    "required": ["python_code"],
                    "properties": {
                        "python_code": {
                            "type": "string",
                            "description": "Python code to perform the requested task while following security constraints."
                        },
                        "python_dependencies": {
                            "type": "array",
                            "description": "Required Python modules (if any).",
                            "items": {
                                "type": "string",
                                "description": "Module name, optionally with version (e.g., 'requests', 'pandas==1.3.0')."
                            }
                        },
                        "security_compliance": {
                            "type": "boolean",
                            "description": "Ensures the generated code follows security policies (restricts access to /data and prevents file deletions).",
                            "enum": [True]
                        }
                    }
                }
            }
        }
        task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
        task_name = "_".join(task.split()[:4])  # Take first 4 words of the task
        filename = f"{task_name}{task_hash}.py".replace(" ", "")

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": B_prompt
                },
                {
                    "role": "user",
                    "content": task
                }
            ],
            "response_format": response_format,
        }

        try:
            response = requests.post(url=url, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for failed requests

            r = response.json()
            print(r)

                    # Extract response content
            content = json.loads(r['choices'][0]['message']['content'])
            python_code = content['python_code']
            python_dependencies = content.get('python_dependencies', [])

                    # Create inline metadata script
            inline_metadata_script = f"""# /// script\n# requires-python = ">=3.8"\n# dependencies = [\n{''.join(f"# \"{dep}\",\n" for dep in python_dependencies)}#\n# ]\n# ///\n"""
            with open(f"{filename}", "w") as f:
                f.write(inline_metadata_script)
                f.write(python_code)

            subprocess.run(["uv", "run", filename])

            return {"filename": filename,"python_code": python_code,"dependencies": python_dependencies}

        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

        except KeyError:
            return {"error": "Unexpected API response format"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)