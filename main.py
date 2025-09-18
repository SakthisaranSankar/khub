import os
from datetime import date, timedelta
import datetime
import mysql.connector
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging, json, time, re
import requests
from dotenv import load_dotenv
from model import SearchRequest, TagRequest
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

FILTER_FIELDS = [
    "legal_entity",
    "divisions",
    "employee_types",
    "departments"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# def get_connection():
#     return mysql.connector.connect(
#         user=os.getenv("SQL_USER"),
#         password=os.getenv("SQL_PASSWORD"),
#         host=os.getenv("SQL_HOST"),
#         port=int(os.getenv("SQL_PORT")),
#         database=os.getenv("SQL_DB")
#     )
#
# def init_db():
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS conversations (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             request_id VARCHAR(255) NOT NULL,
#             role VARCHAR(10) NOT NULL,
#             message TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     """)
#     conn.commit()
#     conn.close()
#
# init_db()
#
# def save_convo(request_id: str, role: str, message: str):
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO conversations (request_id, role, message)
#         VALUES (%s, %s, %s)
#     """, (request_id, role, message))
#     conn.commit()
#     conn.close()
#
# def get_convo(request_id: str, limit: int = 10):
#     conn = get_connection()
#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("""
#         SELECT role, message
#         FROM conversations
#         WHERE request_id = %s
#         ORDER BY created_at DESC
#         LIMIT %s
#     """, (request_id, limit * 2))
#     data = cursor.fetchall()
#     conn.close()
#     return data[::-1]

@app.get("/ping")
async def ping():
    return JSONResponse(content={"message": "pong"})


@app.post("/get_tags")
def get_tags(data: TagRequest):
    file_name = data.values[0].data.fileName
    recordId = data.values[0].recordId
    response_json = {
        'values': []
    }
    try:
        connection = mysql.connector.connect(
            user=os.getenv("SQL_USER"),
            password=os.getenv("SQL_PASSWORD"),
            host=os.getenv("SQL_HOST"),
            port=int(os.getenv("SQL_PORT")),
            database=os.getenv("SQL_DB")
        )

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM document WHERE filename = %s", (file_name,))
        result = cursor.fetchone()
        if not result:
            return JSONResponse(status_code=404, content={"error": "Document not found"})
        tags = {}
        tag_array = json.loads(result['tags'])

        for i, tag in enumerate(tag_array):
            if i < len(FILTER_FIELDS):
                tags[FILTER_FIELDS[i]] = [tag]

        response_json["values"].append({
            "recordId": recordId,
            "data": tags,
            "errors": "",
            "warnings": ""
        })
        return response_json

    except Exception as ex:
        response_json["values"].append({
            "recordId": "1",
            "data": {
                "tags": {}
            },
            "errors": str(ex),
            "warnings": str(ex)
        })
        return JSONResponse(status_code=500, content=response_json)


AI_SEARCH_ENDPOINT = os.getenv("AI_SEARCH_ENDPOINT")
AI_SEARCH_INDEX = os.getenv("AI_SEARCH_INDEX")
AI_SEARCH_API_KEY = os.getenv("AI_SEARCH_API_KEY")
AI_SEARCH_API_VERSION = os.getenv("AI_SEARCH_API_VERSION")
AI_SEARCH_FIELDS = os.getenv("AI_SEARCH_FIELDS", None)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_URL = os.getenv("OPENAI_API_URL")

BASE_IMAGE_URL = os.getenv("BASE_IMAGE_URL")
IMAGE_PREVIEW_TOKEN = os.getenv("IMAGE_PREVIEW_TOKEN")
FILE_PREVIEW_TOKEN = os.getenv("FILE_PREVIEW_TOKEN")


def build_ai_search_filters(filters):
    if not len(filters) == len(FILTER_FIELDS):
        raise HTTPException(status_code=400, detail="Invalid Filters")

    final_filters = []
    for i, field in enumerate(FILTER_FIELDS):
        filter_value = filters[i]
        if filter_value not in [None, ""] and i == (len(FILTER_FIELDS) - 1):
            department_filter_value = filter_value.split('-')[0]
            final_filters.append(f"{field}/any(d:search.in(d, 'General,{filter_value},{department_filter_value}',','))")
        elif filter_value not in [None, ""]:
            final_filters.append(f"{field}/any(d:search.in(d, 'General,{filter_value}',','))")
        else:
            final_filters.append(f"{field}/any(d:search.in(d, 'General'))")

    return " and ".join(final_filters) if final_filters else None


def search_azure(query: str, top_k: int, filters: list[str]):
    """Fetch top_k relevant document chunks from Azure Cognitive Search."""
    url = f"{AI_SEARCH_ENDPOINT}/indexes/{AI_SEARCH_INDEX}/docs/search?api-version={AI_SEARCH_API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "api-key": AI_SEARCH_API_KEY
    }
    payload = {
        "search": query,
        "top": top_k,
        "vectorQueries": [
            {
                "kind": "text",
                "text": query,
                "fields": "chunk_vector"
            }
        ],
        "queryType": "semantic",
        "semanticConfiguration": "semantic-config"
    }
    if not AI_SEARCH_FIELDS is None:
        payload["select"] = AI_SEARCH_FIELDS

    payload["filter"] = build_ai_search_filters(filters)

    start_time = time.perf_counter()
    response = requests.post(url, headers=headers, json=payload)
    response = response.json()

    if "error" in response:
        response["value"] = []
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'time taken to fetch chuncks - {total_time}')
    value=[]
    rerankerScore=float(os.getenv("confidenceFactor",'2.0'))
    for i in response.get("value", []):
        if i['@search.rerankerScore']>= rerankerScore:
            value.append(i)

    print(f'chunks with confidenceFactor - {rerankerScore} , chunk length - {len(value)} chunk - {value}')
    return value


def prompt_builder(query, chunks, tags, conversation_content=None):
    with open("./prompt/system_prompt.txt", 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    # Compute dynamic values
    chunks = json.dumps(chunks)
    conversation_content=json.dumps(conversation_content)
    today = date.today()
    current_year = today.year
    last_year = current_year - 1

    # Calculate last quarter
    current_month = today.month
    last_quarter = ((current_month - 1) // 3) or 4
    if last_quarter == 4:
        last_quarter_year = current_year - 1
    else:
        last_quarter_year = current_year
    last_quarter_str = f"Q{last_quarter} {last_quarter_year}"

    # Replace placeholders
    system_prompt = system_prompt.replace("<<CONVERSATION_HISTORY>>", conversation_content)
    system_prompt = system_prompt.replace("<<last_year>>", str(last_year))
    system_prompt = system_prompt.replace("<<last_quarter>>", last_quarter_str)
    system_prompt = system_prompt.replace("<<current_year>>", str(current_year))
    system_prompt = system_prompt.replace("<<today>>", today.strftime("%A, %Y-%m-%d"))
    system_prompt = system_prompt.replace("<<CHUNKS>>", "\n".join(chunks))
    system_prompt = system_prompt.replace("<<query>>", query)
    system_prompt = system_prompt.replace("<<TAGS>>", str(tags))

    return system_prompt


def call_llm(query: str, chunks: list, tags: list[str], convo_context: list):
    """fields to replace
    1. <<conversation_content>>
    2. <<last_year>>
    3. <<last_quarter>>
    4. <<current_year>>
    5.  <<today>>
    6. <<CHUNKS>>
    7. <<query>>
    """
    system_prompt = prompt_builder(query, chunks, tags,conversation_content=convo_context)
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt}
        ],
        "temperature": 0.2
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    start_time = time.perf_counter()
    response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
    response = response.json()
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'time taken to process chunks - {total_time}')

    llm_response = response
    try:
        # Extract assistant message
        content = llm_response['choices'][0]['message']['content']
        # Ensure valid JSON
        content = content.replace("```json", "").replace("```", "").strip()
        print(content)
        return json.loads(content)
    except Exception as e:
        print(str(e))


def build_page_image(document_key: str, pageNumber: int):
    """Construct pageImage URL based on fileUrl and page number."""

    pageNumber = pageNumber - 1
    return f"{BASE_IMAGE_URL}/{document_key}/normalized_images_{pageNumber}.jpg?{IMAGE_PREVIEW_TOKEN}"


def pre_process_chunk(chunk):
    contexts = []
    sources = []
    for chunkId,i in enumerate(chunk):
        contexts.append({"page_keyphrases": (i["page_keyphrases"]), "page_headings": (i["page_headings"]),
                         "chunk_text": (i["chunk_text"]), "metadata_storage_name": (i["metadata_storage_name"]),
                         # "page_number": (i["page_number"]),
                         'metadata_storage_last_modified': i['metadata_storage_last_modified'],
                         "chunkId":chunkId+1
                         })

        sources.append({"fileName": i['metadata_storage_name'],
                        "fileUrl": f'{i['metadata_storage_path']}?{FILE_PREVIEW_TOKEN}',
                        'pageNumber': i["page_number"],
                        "document_key": i['document_key'],
                        "lastUpdatedDate": i["metadata_storage_last_modified"],
                        "pageImage": build_page_image(i['document_key'], i["page_number"]),
                        "chunkId":chunkId+1
                        })
    return {"contexts": contexts, "sources": sources}


def post_process_context(context:list,chunkid:list):
    out=[]
    print()
    for i in context:
        if i['chunkId'] in chunkid:
            out.append(i)

    return out

def get_documents(src):
    seen = set()
    docs = []
    for i in src:
        if i['fileUrl'] not in seen:
            seen.add(i['fileUrl'])
            docs.append({
                'fileName': i['fileName'],
                'fileUrl': i['fileUrl']
            })
    return docs


def get_images(src):
    seen = set()
    img = []
    for i in src:
        key = (i['fileName'], i['pageNumber'])
        if key not in seen:
            seen.add(key)
            img.append({
                "pageNumber": i['pageNumber'],
                "url": i['pageImage']
            })
    return img


@app.post("/search")
def search(data: SearchRequest):
    logging.info('Python HTTP trigger function processed a request.')
    body = data
    query = body.query
    top_k = body.top_k
    filters = body.filters
    user_id=body.userId
    filters = [filters.legalEntity, filters.divisions, filters.employeeTypes, filters.departments]


    chunks = search_azure(query, top_k, filters)
    convo_context=[]
    # convo_context=get_convo(user_id,10)
    print(convo_context)
    context = pre_process_chunk(chunks)
    answer_json = call_llm(query, context['contexts'], filters,convo_context)

    # save_convo(user_id,"Bot",answer_json['answer'])
    # save_convo(user_id, "User", query)
    print(answer_json['relevantAnswer'] == 'true' or answer_json['relevantAnswer'] == True)
    if answer_json['relevantAnswer'] == 'true' or answer_json['relevantAnswer'] == True:
        answer_json['sources'] = context['sources']
        final_context=post_process_context(context['sources'],answer_json['usedChunkIDs'])
        answer_json["tags"]= filters
        answer_json["documents"] = get_documents(final_context)
        answer_json["images"] = get_images(final_context)
        if len(context['contexts'])==0:
            answer_json['suggestedQuestions'] = []
    else:
        answer_json['sources'] = []
        answer_json["documents"] = []
        answer_json["images"] = []
        answer_json['suggestedQuestions'] = []
    return JSONResponse(content=answer_json)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
