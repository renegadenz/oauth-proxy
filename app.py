from aws_cdk import App
from oauth_proxy.oauth_proxy_stack import OAuthProxyStack  # Note the capital 'A'

app = App()
OAuthProxyStack(app, "OAuthProxyStack")
app.synth()
