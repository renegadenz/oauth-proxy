import json
import requests
import os
import boto3

def lambda_handler(event, context):
    # Retrieve the ServiceDesk Plus API key from Secrets Manager
    service_desk_api_key = os.environ['SERVICE_DESK_API_KEY']
    
    # Datadog webhook body (e.g., alert or event data)
    body = json.loads(event['body'])
    title = body.get('title', 'Datadog Alert')
    message = body.get('message', 'No details provided')
    
    # ServiceDesk Plus API URL to create a new ticket
    servicedesk_url = "https://your-servicedesk-url/sdpapi/request"
    
    # Construct the ServiceDesk Plus ticket payload
    payload = {
        "subject": title,
        "description": message,
        "requester": {"name": "Datadog Monitor"},
        "priority": "High"
    }

    # Headers for ServiceDesk Plus API call (use the API key from Secrets Manager)
    headers = {
        "Authorization": f"ApiKey {service_desk_api_key}",
        "Content-Type": "application/json"
    }

    # Send the request to ServiceDesk Plus API
    response = requests.post(servicedesk_url, json=payload, headers=headers)

    if response.status_code == 200:
        return {
            'statusCode': 200,
            'body': json.dumps("Incident successfully created in ServiceDesk Plus")
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to create incident: {response.text}")
        }
