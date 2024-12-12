# OAuth Proxy CDK Project
This project defines an AWS CDK application for integrating Datadog with ServiceDesk Plus using an OAuth2 proxy via Amazon Cognito, API Gateway, Lambda, and Secrets Manager.

## Overview
This CDK project automates the deployment of the following AWS resources:

Cognito: Authenticates Datadog using OAuth2 before making requests to API Gateway.
API Gateway: Exposes an HTTP endpoint that Datadog can send webhooks to.
Lambda: Handles the business logic of receiving Datadog webhooks, authenticating to ServiceDesk Plus, and creating/updating tickets using ServiceDesk Plus' API.
Secrets Manager: Stores sensitive information such as Datadog OAuth2 credentials and the ServiceDesk Plus API key securely.
Prerequisites
Before deploying the stack, ensure that you have the following set up:

AWS Account: You must have an AWS account with appropriate permissions to deploy resources using AWS CDK.

AWS CLI: Set up and configured with aws configure.

CDK CLI: Install the AWS CDK command-line tool globally:

```
npm install -g aws-cdk
Python 3.x: This project is set up with Python 3.x. Make sure you have it installed along with pip and virtualenv.
```

### Project Setup
Clone the repository:

Clone this repository to your local machine:

```
git clone https://github.com/renegadenz/oauth-proxy
cd oauth_proxy
```
Create the virtual environment:

Use the following commands to create and activate a virtual environment for the project:

On Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```
On Windows:

```
python -m venv .venv
.venv\Scripts\activate.bat
```
Install the dependencies:

Install the required Python dependencies using pip:

```
pip install -r requirements.txt
```
Configuration
Secrets Manager:

The ServiceDesk Plus API key and Datadog OAuth2 credentials are stored in AWS Secrets Manager.
Secrets should be created manually or updated as follows:
ServiceDesk Plus API Key: Store this key in Secrets Manager under SERVICE_DESK_API_KEY with a key serviceDeskApiKey.
Datadog OAuth2 Credentials: Store the clientId and clientSecret for Datadog in Secrets Manager under DATADOG_OAUTH_CREDENTIALS.
Cognito:

The Cognito User Pool is used to authenticate Datadog using OAuth2.
During deployment, CDK will set up a Cognito User Pool and a User Pool Client to enable Datadog authentication.
Lambda:

The Lambda function listens to webhooks from Datadog and uses the ServiceDesk Plus API key (from Secrets Manager) to interact with ServiceDesk Plus's API to create or update tickets.
CDK Deployment Commands
List all stacks:

This will display all the stacks in your CDK app:

```
cdk ls
```
Synthesizing CloudFormation template:

This command generates the CloudFormation template from the CDK code:


```
cdk synth
```
Deploy the stack:

This command deploys the stack to your AWS account and region:
```
cdk deploy
```
If you haven't set the environment (env), the stack will be deployed to the default AWS account and region configured in your CLI. You can also specify a specific environment by uncommenting the env line in app.py.
Compare with deployed stack:

Use this to compare the current state of the stack with what is deployed:

```
cdk diff
```
Open CDK Documentation:

This command opens the AWS CDK documentation:
```
cdk docs
```
Configuration in app.py
In the app.py file, you can configure the AWS environment (account and region) where the stack will be deployed. You can either use the default AWS configuration or specify your account and region explicitly.

```
app = cdk.App()
```

# If you want to use the default AWS CLI configuration
OauthProxyStack(app, "OauthProxyStack")

# Or if you want to specify a specific account and region, uncomment and modify:
# env=cdk.Environment(account='123456789012', region='us-east-1')
Lambda Function Code
The Lambda function (datadog_to_servicedesk_proxy.py) processes webhooks from Datadog and interacts with ServiceDesk Plus using the ServiceDesk Plus API key retrieved from Secrets Manager. Here's a brief overview of how it works:

It receives a Datadog webhook containing alert information.
It authenticates to ServiceDesk Plus using the API key and creates or updates a ticket with the details from the webhook.
Deploying the Solution
Set Up Secrets in AWS Secrets Manager:

ServiceDesk Plus API Key: Store it under SERVICE_DESK_API_KEY with the key serviceDeskApiKey.
Datadog OAuth2 Credentials: Store it under DATADOG_OAUTH_CREDENTIALS with the keys clientId and clientSecret.
Deploy: After setting up the environment, run the following command to deploy your resources:

```
cdk deploy
```
Once the deployment is successful, API Gateway will expose a URL, and Datadog will be able to send webhooks to this endpoint.

## Debugging and Logs
You can view the logs of your Lambda function and API Gateway using CloudWatch to debug any issues related to requests or responses.

### Additional Notes
Ensure that your AWS credentials are configured using aws configure or that your environment variables (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) are set for deployment.
The Lambda function relies on the ServiceDesk Plus API key being correctly set up in Secrets Manager. If the Lambda doesn't have access to the correct API key, it will fail to interact with ServiceDesk Plus.
The OAuth2 flow for Datadog relies on Cognito for authentication before the webhook is processed by API Gateway.
