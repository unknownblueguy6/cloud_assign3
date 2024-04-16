import boto3
import json
import requests
import os
import hashlib
from opensearchpy import OpenSearch

client = boto3.client('lexv2-runtime')
rekognition_client = boto3.client('rekognition')
os_domain = 'search-photos-qa7gktwgjplnxsefhwwci7xl2u.aos.us-east-1.on.aws'
os_index = 'photos'
auth = (os.environ.get("OS_USER"), os.environ.get("OS_PASS"))

os_client = OpenSearch(
        hosts = [{'host': os_domain, 'port':443,}],
        http_compress = True,
        use_ssl = True,
        verify_certs = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False
)


def make_query(labels):
    query = {
        "query": {
            "bool": {
                "should": [
                    {"term": {"labels": label}} for label in labels
                ],
                "minimum_should_match": 1
            }
        },
        "sort": [
            {
                "_score": {"order": "desc"}
            }
        ]
    }

    response = os_client.search(
        body = query,
        index = os_index
    )
    
    results = []

    if response['hits']['total']['value'] > 0:
        for hit in response['hits']['hits']:
            s3_url = f"https://s3.amazonaws.com/{hit['_source']['bucket']}/{hit['_source']['objectKey']}"
            labels = hit['_source']['labels']
            results.append({'url': s3_url, 'labels': labels})

    print(results)
    return results


def lambda_handler(event, context):
    print(event)

    q = event['queryStringParameters']['q']
    print(q)
    
    # Specify your Lex V2 bot details
    bot_id = "UBYYIGGUJO"  
    bot_alias_id = "TSTALIASID"  
    locale_id = "en_US"  
    session_id = event.get('sessionId', 'testuser')
    
    user_message = q
    
    response = client.recognize_text(
        botId=bot_id,
        botAliasId=bot_alias_id,
        localeId=locale_id,
        sessionId=session_id,
        text=user_message,
        # session_attributes = {}
    )

    slots = []
    try:
        for interpretation in response['interpretations']:
            intent = interpretation.get('intent', {})
            if intent.get('name') == 'SearchIntent':
                slot_values = intent.get('slots', {})
                for key, slot in slot_values.items():
                    if slot and slot.get('value'):
                        slots.append(slot['value']['interpretedValue'])
    except Exception as e:
        print(f"Error extracting slots: {str(e)}")
        
    if len(slots) == 0:
        return {
        "statusCode": 400,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({"code":400, "message":"could not get key"})
    }

    print("Extracted Slots:", slots)
    
    print(f"OpenSearch client: {os_client}")
    unique_labels = list(set(slots))
    print(f"Unique labels: {unique_labels}")
    
    results = make_query(unique_labels)
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET"
        },
        "body": json.dumps({"results":results})
    }