import os
import json
import boto3
import requests
import time
import sys
from urllib.parse import urlencode
from botocore.exceptions import ClientError

def get_secret():
    """Retrieve credentials from AWS Secrets Manager"""
    secret_name = os.environ['SERVICEDESK_SECRET_NAME']
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except ClientError as e:
        raise Exception(f"Error retrieving secret: {e}")

def update_secret(secret):
    """Update the secret in AWS Secrets Manager with new access token"""
    secret_name = os.environ['SERVICEDESK_SECRET_NAME']
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    try:
        client.put_secret_value(SecretId=secret_name, SecretString=json.dumps(secret))
    except ClientError as e:
        raise Exception(f"Error updating secret: {e}")

def renew_access_token(secret):
    """Renew the OAuth access token using a refresh token"""
    refresh_token = secret['refresh_token']
    client_id = secret['client_id']
    client_secret = secret['client_secret']

    # Fetch token URL and redirect URI from environment variables
    token_url = os.environ.get('TOKEN_URL')
    redirect_uri = os.environ.get('REDIRECT_URI')

    print("\nRenewing access token...", file=sys.stdout)

    payload = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }

    response = requests.post(token_url, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'}, verify=False)
    response_data = response.json()

    print("\nOAuth Response:", json.dumps(response_data, indent=2), file=sys.stdout)

    if response.status_code == 200 and 'access_token' in response_data:
        print("\nAccess token successfully renewed!", file=sys.stdout)
        access_token = response_data['access_token']
        secret['access_token'] = access_token
        secret['token_expiry'] = int(time.time()) + response_data.get('expires_in', 3600)  # Default 1-hour expiry

        # Save new access token in AWS Secrets Manager
        update_secret(secret)

        return access_token
    else:
        print("\nFailed to renew access token.", file=sys.stdout)
        raise Exception(f"Failed to renew access token: {response_data}")

def get_valid_access_token(secret):
    """Check if the current token is expired and renew if necessary"""
    access_token = secret.get('access_token')
    token_expiry = secret.get('token_expiry', 0)

    if not access_token or token_expiry <= int(time.time()):
        print("\nToken expired, renewing...", file=sys.stdout)
        return renew_access_token(secret)

    return access_token

def lambda_handler(event, context):
    """
    AWS Lambda function that processes webhook events from API Gateway.
    Extracts the body payload, submits it as `input_data` to ServiceDesk Plus.
    Automatically renews access tokens if expired.
    """

    try:
        # Retrieve ServiceDesk Plus credentials from AWS Secrets Manager
        secret = get_secret()
        servicedesk_url = os.environ.get('SERVICEDESK_URL', secret.get('url'))  # Use ENV variable or fallback to Secrets Manager

        # Renew access token if needed
        access_token = get_valid_access_token(secret)

        # Extract the `body` from API Gateway event
        if 'body' in event:
            try:
                request_body = json.loads(event['body'])  # Parse the request body
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON format in request body'}),
                    'headers': {'Content-Type': 'application/json'}
                }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing request body'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Ensure `input_data` exists in the request body
        if "input_data" in request_body:
            input_data = request_body["input_data"]
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing input_data in request body'}),
                'headers': {'Content-Type': 'application/json'}
            }

        headers = {
            'Accept': 'application/vnd.manageengine.sdp.v3+json',
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Pass the extracted `input_data` as a URL-encoded string
        data = urlencode({"input_data": json.dumps(input_data)})

        print("\nSending request to ServiceDesk Plus...", file=sys.stdout)

        response = requests.post(servicedesk_url, headers=headers, data=data)

        # Log response for debugging
        print("\nServiceDesk Plus API Response:", file=sys.stdout)
        print(response.text, file=sys.stdout)

        if response.status_code == 200:
            print("Request successfully created!", file=sys.stdout)
            return {
                'statusCode': 200,
                'body': json.dumps(response.json()),
                'headers': {'Content-Type': 'application/json'}
            }
        else:
            print(f"Failed to create request: {response.status_code}", file=sys.stdout)
            return {
                'statusCode': response.status_code,
                'body': response.text,
                'headers': {'Content-Type': 'application/json'}
            }

    except Exception as e:
        print(f"\nError: {e}", file=sys.stdout)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
