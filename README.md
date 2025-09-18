# khub

#OPENAI_API_KEY
#AI_SEARCH_API_KEY
#IMAGE_PREVIEW_TOKEN
#FILE_PREVIEW_TOKEN



curl --location 'https://api-talk-to-your-document-cdgfa3fcbcfrc9bv.uaenorth-01.azurewebsites.net/search' \
--header 'Content-Type: application/json' \
--data '{
    "query": "tell me about adib",
    "top_k": 10,
    "userId":"123",
    "filters": {
        "legalEntity": "ADIB", 
        "divisions": "General",
        "employeeTypes": "FTE",
        "departments": "TEC-Cloud Solutions"
    }
}'





curl --location 'https://aisearch-talktoyourdocument.search.windows.net/indexes/index-talktoyourdocuments/docs/search?api-version=2024-07-01' \
--header 'Content-Type: application/json' \
--header 'api-key: GsX00lDAD150RXTeiYP896djyuRO0sLLtnT8PxisYKAzSeCOatbu' \
--data '{
    "search": "good morning",
    "top": 10,
    
    "vectorQueries": [
        {
            "kind": "text",
            "text": "good morning",
            "fields": "chunk_vector"
        }
    ],
    "queryType": "semantic",
    "semanticConfiguration": "semantic-config",
      "select": "metadata_storage_name,metadata_storage_path,page_number,document_key,chunk_text,id,metadata_storage_last_modified,divisions,legal_entity,departments,employee_types,page_headings,page_keyphrases",
    "filter": "legal_entity/any(d:search.in(d, '\''General,General'\'','\'','\'')) and divisions/any(d:search.in(d, '\''General,ADIB'\'','\'','\'')) and employee_types/any(d:search.in(d, '\''General,General'\'','\'','\'')) and departments/any(d:search.in(d, '\''General,General,General'\'','\'','\''))"
    
}'
