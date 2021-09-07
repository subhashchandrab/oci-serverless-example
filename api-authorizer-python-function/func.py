import io
import json
import logging
import datetime

from datetime import timedelta
from fdk import response

def handler(ctx, data: io.BytesIO = None):
    auth_token = ""
    token = ""
    apiKey = ""
    # Set the expiry as 2 minutes from the current time
    expiresAt = (datetime.datetime.utcnow() + timedelta(seconds=120)).replace(tzinfo=datetime.timezone.utc).astimezone().replace(microsecond=0).isoformat()
    
    try:
        requestbody_str = data.getvalue().decode('UTF-8')
        if requestbody_str:
            auth_token = json.loads(requestbody_str)
            token = auth_token.get("token")
        
            app_context = dict(ctx.Config())
            apiKey = app_context['PRODUCT_STORE_API_KEY']
        
            if token == apiKey:
                return response.Response(
                    ctx, 
                    status_code=200, 
                    response_data=json.dumps({"active": True, "principal": "foo", "scope": "bar", "clientId": "1234", "expiresAt": expiresAt, "context": {"username": "wally"}})
                )
        else:
           print("request body is empty", flush=True)
    
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))
        pass
    
    return response.Response(
        ctx, 
        status_code=401, 
        response_data=json.dumps({"active": False, "wwwAuthenticate": "API-key"})
    )
