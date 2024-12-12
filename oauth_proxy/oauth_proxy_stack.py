from aws_cdk import (
    App,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_cognito as cognito,
)
from constructs import Construct

class OAuthProxyStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Secrets for ServiceDesk Plus API Key
        servicedesk_api_key = secretsmanager.Secret(self, "ServiceDeskApiKey", 
            secret_name="SERVICE_DESK_API_KEY",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="serviceDeskApiKey",
                password_length=32,
            )
        )

        # Secrets for Datadog OAuth2 credentials
        datadog_oauth_credentials = secretsmanager.Secret(self, "DatadogOAuthCredentials", 
            secret_name="DATADOG_OAUTH_CREDENTIALS",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="clientSecret",
                password_length=32,
            )
        )

        # Cognito User Pool for Authentication
        cognito_user_pool = cognito.UserPool(self, "DatadogServiceDeskUserPool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            user_pool_name="DatadogServiceDeskUserPool",
            lambda_triggers=None,
        )

        # Cognito User Pool Client (to authenticate users)
        cognito_user_pool_client = cognito.UserPoolClient(self, "DatadogServiceDeskUserPoolClient",
            user_pool=cognito_user_pool,
            generate_secret=True,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )

        # Lambda function: Datadog to ServiceDesk Plus Proxy
        datadog_to_servicedesk_function = _lambda.Function(self, "DatadogToServiceDeskProxy",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="datadog_to_servicedesk_proxy.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "SERVICE_DESK_API_KEY": servicedesk_api_key.secret_value_from_json("serviceDeskApiKey").to_string(),
                "DATADOG_OAUTH_CLIENT_ID": datadog_oauth_credentials.secret_value_from_json("clientId").to_string(),
                "DATADOG_OAUTH_CLIENT_SECRET": datadog_oauth_credentials.secret_value_from_json("clientSecret").to_string(),
            },
        )

        # Lambda execution role
        datadog_to_servicedesk_function.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue", "logs:*", "cloudwatch:*"],
                resources=["*"]
            )
        )

        # API Gateway for Datadog to ServiceDesk Plus Proxy
        api_gateway = apigateway.RestApi(self, "DatadogToServiceDeskApi",
            rest_api_name="DatadogToServiceDeskPlusProxy",
            description="API Gateway for Datadog to ServiceDesk Plus Proxy Integration"
        )

        # Integrating Cognito authentication for API Gateway
        api_gateway.add_authorizer(
            cognito_user_pool_authorizer=cognito.CognitoUserPoolsAuthorizer(self, "DatadogServiceDeskAuthorizer",
                cognito_user_pool=cognito_user_pool,
            )
        )

        datadog_to_servicedesk_resource = api_gateway.root.add_resource("datadog-to-servicedesk")
        datadog_to_servicedesk_resource.add_method("POST", apigateway.LambdaIntegration(datadog_to_servicedesk_function),
                                                  authorizer=api_gateway.authorizer)

        # Create API Key
        api_key = api_gateway.add_api_key("IntegrationApiKey", api_key_name="IntegrationApiKey")
        usage_plan = api_gateway.add_usage_plan("UsagePlan",
            name="ServiceIntegrationUsagePlan",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10, burst_limit=20
            ),
            quota=apigateway.QuotaSettings(
                limit=1000, period=apigateway.Period.MONTH
            ),
        )
        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(stage=api_gateway.deployment_stage)

        # Output the URL for the deployed API Gateway
        self.output_api_url(api_gateway)

    def output_api_url(self, api_gateway: apigateway.RestApi):
        output_url = f"https://{api_gateway.rest_api_id}.execute-api.{self.region}.amazonaws.com/{api_gateway.deployment_stage.stage_name}"
        output_url_cfn = self.node.default_child
        output_url_cfn.add_property_override("Outputs.ApiUrl.Value", output_url)


app = App()
OAuthProxyStack(app, "OAuthProxyStack")
app.synth()
