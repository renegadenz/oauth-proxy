import os
import json
import boto3
import requests
from botocore.exceptions import ClientError

def get_secret():
    secret_name = os.environ['SERVICEDESK_SECRET_NAME']
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except ClientError as e:
        raise e

def lambda_handler(event, context):
    try:
        # Get ServiceDesk Plus configuration from Secrets Manager
        secret = get_secret()
        servicedesk_api_key = secret['api_key']
        servicedesk_url = secret['url']

        # Process Datadog webhook payload
        webhook_payload = json.loads(event['body'])
        
        # Make request to ServiceDesk Plus with API key
        headers = {
            'Authorization': f'ApiKey {servicedesk_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{servicedesk_url}/api/v3/requests",  # Adjust endpoint as needed
            headers=headers,
            json=webhook_payload
        )
        
        return {
            'statusCode': response.status_code,
            'body': json.dumps(response.json()),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
