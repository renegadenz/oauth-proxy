import json
from datetime import datetime

def lambda_handler(event, context):
    # Log the full event
    print("Full event:", json.dumps(event))
    
    try:
        # Parse and log the body
        body = json.loads(event['body']) if event.get('body') else {}
        print("Parsed body:", json.dumps(body))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Webhook received and logged',
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
