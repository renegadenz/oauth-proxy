#!/usr/bin/env python3
import os
import aws_cdk as cdk
from oauth_proxy.oauth_proxy_stack import OauthProxyStack

app = cdk.App()

# You can use environment-specific configuration by passing an 'env' parameter
OauthProxyStack(app, "OauthProxyStack",
    # Uncomment the following lines to specify the AWS Account and Region
    # account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    # region=os.getenv('CDK_DEFAULT_REGION'),
    
    # OR specify a specific environment directly like this:
    # env=cdk.Environment(account='123456789012', region='us-east-1'),
)

# Synthesizes the CloudFormation template
app.synth()
