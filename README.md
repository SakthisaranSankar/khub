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
