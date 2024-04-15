import boto3
import json
import requests
import os
import hashlib
from opensearchpy import OpenSearch

# Initialize the S3 and Rekognition clients
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

# Assume Elasticsearch domain URL and index are defined
os_domain = 'search-photos-qa7gktwgjplnxsefhwwci7xl2u.aos.us-east-1.on.aws'
os_index = 'photos'
auth = (os.environ.get("OS_USER"), os.environ.get("OS_PASS"))

os_client = OpenSearch(
        hosts = [{'host': os_domain, 'port':443,}],
        http_compress = True, # enables gzip compression for request bodies
        http_auth = auth,
        use_ssl = True,
        verify_certs = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False
)


def hash_string(input_string):
    # Create a hashlib object
    hasher = hashlib.sha256()
    
    # Update the hasher with the input string
    hasher.update(input_string.encode('utf-8'))
    
    # Get the hexadecimal representation of the hash
    hashed_output = hasher.hexdigest()
    
    return hashed_output

def index_document(doc):
    return os_client.index(index=os_index, body=doc, id=hash_string(doc["objectKey"]))
    # url = f"https://{os_domain}/{os_index}/_doc"
    # response = requests.post(url, json=doc, auth=auth)
    # return response.json()

def lambda_handler(event, context):
    
    # Get the bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    # print(f"Bucket: {bucket_name}, Object Key: {object_key}")
    print(f"Debug Event: {event}")
    
    # Retrieve the object's metadata
    metadata_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
    metadata = metadata_response.get('Metadata', {})
    # print(metadata)
    # Extract the 'customlabels' metadata, if it exists
    custom_labels_str = metadata.get('customlabels')  # Metadata keys are lowercase
    custom_labels = custom_labels_str.split(',') if custom_labels_str else []
    custom_labels = [label.strip() for label in custom_labels]
    print(f"Custom Labels: {custom_labels}")

    # Create a JSON array with the labels
    labels_json_array = json.dumps(custom_labels)
    print(f"Custom Labels for {object_key} (JSON Array): {labels_json_array}")

    
    # Call Rekognition to detect labels in the image
    response = rekognition_client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_key
            }
        },
        MaxLabels = 10
    )
    
    print(response)

    # Process Rekognition response and extract labels
    rekognition_labels = [label_data['Name'] for label_data in response['Labels']]
    
    # Log the detected labels
    print(f"Detected labels for {object_key}: {rekognition_labels}")
    
    labels = custom_labels + rekognition_labels
    
    print(f"All labels for {object_key}: {labels}")

    
    # Example document
    document = {
        "objectKey": object_key,
        "bucket": bucket_name,
        "labels": labels,  # Assume this includes both Rekognition and custom labels
        "createdTimestamp": metadata_response['LastModified'].isoformat()  # From S3 head_object
    }

    # Index the document in Elasticsearch
    index_response = index_document(document)
    print(f"Elasticsearch index response: {index_response}")



    # Here, you would typically continue to process these labels, 
    # such as indexing them in Elasticsearch

    return {
        'statusCode': 200,
        'body': json.dumps('Image indexing complete.')
    }
