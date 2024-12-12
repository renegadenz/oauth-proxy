from aws_cdk import (
    App,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_cognito as cognito,
    CfnOutput,
)
from constructs import Construct

class OAuthProxyStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Secrets for ServiceDesk Plus API Key
        servicedesk_api_key = secretsmanager.Secret(
            self, 
            "ServiceDeskApiKey",
            secret_name="SERVICE_DESK_API_KEY",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="serviceDeskApiKey",
                password_length=32,
            )
        )

        # Secrets for Datadog OAuth2 credentials
        datadog_oauth_credentials = secretsmanager.Secret(
            self, 
            "DatadogOAuthCredentials",
            secret_name="DATADOG_OAUTH_CREDENTIALS",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="clientSecret",
                password_length=32,
            )
        )

        # Cognito User Pool for Authentication
        cognito_user_pool = cognito.UserPool(
            self,
            "DatadogServiceDeskUserPool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            user_pool_name="DatadogServiceDeskUserPool",
        )

        # Cognito User Pool Client
        cognito_user_pool_client = cognito.UserPoolClient(
            self,
            "DatadogServiceDeskUserPoolClient",
            user_pool=cognito_user_pool,
            generate_secret=True,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )

        # Lambda function: Datadog to ServiceDesk Plus Proxy
        datadog_to_servicedesk_function = _lambda.Function(
            self,
            "DatadogToServiceDeskProxy",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="datadog_to_servicedesk_proxy.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "SERVICE_DESK_API_KEY_SECRET_ARN": servicedesk_api_key.secret_arn,  # Pass ARN here
                "DATADOG_OAUTH_CLIENT_ID_SECRET_ARN": datadog_oauth_credentials.secret_arn,  # Pass ARN for Datadog OAuth client ID
                "DATADOG_OAUTH_CLIENT_SECRET_SECRET_ARN": datadog_oauth_credentials.secret_arn,  # Pass ARN for Datadog OAuth client secret
            },
        )

        # Lambda execution role permissions
        datadog_to_servicedesk_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "logs:*",
                    "cloudwatch:*"
                ],
                resources=["*"]
            )
        )

        # API Gateway
        api = apigateway.RestApi(
            self,
            "DatadogToServiceDeskApi",
            rest_api_name="DatadogToServiceDeskPlusProxy",
            description="API Gateway for Datadog to ServiceDesk Plus Proxy Integration"
        )

        # Create Cognito Authorizer
        cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "DatadogServiceDeskAuthorizer",
            cognito_user_pools=[cognito_user_pool]  # Corrected to use cognito_user_pools
        )

        # Create API resource and method
        datadog_resource = api.root.add_resource("webhook")
        datadog_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(datadog_to_servicedesk_function),
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )

        # Create API Key
        api_key = api.add_api_key(
            "IntegrationApiKey",
            api_key_name="IntegrationApiKey"
        )

        # Create Usage Plan
        usage_plan = api.add_usage_plan(
            "UsagePlan",
            name="ServiceIntegrationUsagePlan",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            ),
            quota=apigateway.QuotaSettings(
                limit=1000,
                period=apigateway.Period.MONTH
            ),
        )

        # Add API Key to Usage Plan
        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(stage=api.deployment_stage)

        # Correct Output for API URL
        CfnOutput(self, "ApiUrl",
            value=f"https://{api.rest_api_id}.execute-api.{self.region}.amazonaws.com/{api.deployment_stage.stage_name}",
            description="The URL of the deployed API Gateway"
        )


app = App()
OAuthProxyStack(app, "OAuthProxyStack")
app.synth()
