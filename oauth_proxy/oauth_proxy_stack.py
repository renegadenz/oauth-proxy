from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_secretsmanager as secrets_manager
)
from constructs import Construct

class OAuthProxyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        cognito_user_pool = cognito.UserPool(
            self,
            "DatadogServiceDeskUserPool",
            self_sign_up_enabled=False,
            user_pool_name="DatadogServiceDeskUserPool",
        )

        # Add domain to user pool
        domain = cognito_user_pool.add_domain(
            "DatadogServiceDeskUserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="datadog-servicedesk"
            )
        )

        # Define resource server with custom scopes for Datadog
        resource_server = cognito.UserPoolResourceServer(
            self,
            "ResourceServer",
            user_pool=cognito_user_pool,
            identifier="datadog-webhook-api",
            scopes=[
                cognito.ResourceServerScope(
                    scope_name="webhook.write",
                    scope_description="Permission to send webhook data"
                )
            ]
        )

        # Configure the client for Datadog
        cognito_user_pool_client = cognito.UserPoolClient(
            self,
            "DatadogServiceDeskUserPoolClient",
            user_pool=cognito_user_pool,
            generate_secret=True,
            auth_flows=cognito.AuthFlow(
                admin_user_password=False,
                custom=False,
                user_password=False,
                user_srp=False
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    client_credentials=True
                ),
                scopes=[cognito.OAuthScope.custom("datadog-webhook-api/webhook.write")]
            )
        )

        # Create API Gateway
        api = apigateway.RestApi(
            self,
            "DatadogServiceDeskApi",
            rest_api_name="datadog-servicedesk-api"
        )

        # Create secret for ServiceDesk Plus credentials
        servicedesk_secret = secrets_manager.Secret(
            self,
            "ServiceDeskCredentials",
            description="Credentials for ServiceDesk Plus"
        )

        # Create Lambda function
        datadog_to_servicedesk_function = lambda_.Function(
            self,
            "DatadogToServiceDeskFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            environment={
                "SERVICEDESK_SECRET_NAME": servicedesk_secret.secret_name
            }
        )

        # Grant Lambda permission to read the secret
        servicedesk_secret.grant_read(datadog_to_servicedesk_function)

        # Create Cognito authorizer with explicit configuration
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "DatadogWebhookAuthorizer",
            cognito_user_pools=[cognito_user_pool],
            identity_source=apigateway.IdentitySource.header('Authorization'),
            results_cache_ttl=Duration.seconds(0)  # Disable caching for testing
        )

        # Create API endpoint with Cognito authorization
        webhook_resource = api.root.add_resource("webhook")
        webhook_integration = apigateway.LambdaIntegration(datadog_to_servicedesk_function)

        # Add method with explicit scope authorization
        webhook_resource.add_method(
            "POST",
            webhook_integration,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer,
            authorization_scopes=["datadog-webhook-api/webhook.write"]
        )

        # Add outputs with unique identifiers
        CfnOutput(
            self,
            "CognitoTokenURL",
            value=f"https://datadog-servicedesk.auth.{self.region}.amazoncognito.com/oauth2/token",
            description="Token endpoint URL"
        )

        CfnOutput(
            self,
            "CognitoClientId",
            value=cognito_user_pool_client.user_pool_client_id,
            description="Client ID"
        )
