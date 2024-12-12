import aws_cdk as core
import aws_cdk.assertions as assertions

from oauth_proxy.oauth_proxy_stack import OauthProxyStack

# example tests. To run these tests, uncomment this file along with the example
# resource in oauth_proxy/oauth_proxy_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = OauthProxyStack(app, "oauth-proxy")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
