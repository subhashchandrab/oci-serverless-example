#
# oci-serverless-demo-python version 1.0.
# This function connects to the ATP database and performs the basic operations
# like Fetch/Create/Update/Delete for the products table

import io
import oci
import base64
import json
import requests
from urllib.parse import urlparse, parse_qs  

from fdk import response

def ords_run_sql(ordsbaseurl, dbschema, dbpwd, sqlQuery):
    dbsqlurl = ordsbaseurl + dbschema + '/_/sql'
    headers = {"Content-Type": "application/sql"}
    auth=(dbschema, dbpwd)
    r = requests.post(dbsqlurl, auth=auth, headers=headers, data=sqlQuery)
    result = {}
    print("status code:", r.status_code, flush=True)
    r_json = json.loads(r.text)
    print("sql REST call response", r_json, flush=True)
#    if r.status_code == 200:
    try:
        for item in r_json["items"]:
            result["sql_statement"] = item["statementText"]
            if "errorDetails" in item:
                result["error"] = item["errorDetails"]
            elif "resultSet" in item:
                result["results"] = item["resultSet"]["items"]
            elif "response" in item:
                result["response"] = item["response"]
    except ValueError:
        print(r.text, flush=True)
        raise
#    else:
#        result["error"] = "Error while invoking the SQL Rest endpoint"
    return result

# get the sql query based on the operation extracted from the request URL parameters
def get_sql_query(requestUrlString, queryString, dbUser):
    tableName = dbUser + ".products"
    sqlQuery = "select name, count from " + tableName
    if "/getProducts" in requestUrlString:
        sqlQuery = "select name, count from " + tableName
    elif "/addProduct" in requestUrlString:
        product_name = queryString['name'][0]
        product_count = int(queryString['count'][0])
        sqlQuery = "insert into "+ tableName + " values ('" + product_name +"' , "+ str(product_count) + ")"
    elif "/updateProduct" in requestUrlString:
        product_name = queryString['name'][0]
        product_count = int(queryString['count'][0])
        sqlQuery = "update "+ tableName +" set count=" + str(product_count) + " where name = '"+product_name+"'" 
    elif "/deleteProduct" in requestUrlString:
        product_name = queryString['name'][0]
        sqlQuery = "delete from "+ tableName + " where name = '"+product_name+"'" 
    return sqlQuery

def read_secret_value(secret_id):
    print("Reading vaule of secret_id: ", secret_id)
    resource_principal_signer = oci.auth.signers.get_resource_principals_signer()
    secret_client = oci.secrets.SecretsClient(config={}, signer=resource_principal_signer)
    response = secret_client.get_secret_bundle(secret_id)

    base64_Secret_content = response.data.secret_bundle_content.content
    base64_secret_bytes = base64_Secret_content.encode('ascii')
    base64_message_bytes = base64.b64decode(base64_secret_bytes)
    secret_content = base64_message_bytes.decode('ascii')

    return secret_content

def handler(ctx, data: io.BytesIO=None):

    # retrieving the request body, e.g. {"key1":"value"}
    try:
        requestbody_str = data.getvalue().decode('UTF-8')
        if requestbody_str:
           print("Headers: " , json.loads(requestbody_str), flush=True) 
        else:
           print("request body is empty", flush=True)
    except Exception as ex:
        print('ERROR: The request body is not JSON', ex, flush=True)
        raise    

    # retrieving the request URL, e.g. "/v1/http-info"
    request_url = ctx.RequestURL()
    request_url_string = json.dumps(request_url)
    print("Request URL: ", request_url_string, flush=True)
    
    # retrieving query string from the request URL, e.g. {"param1":["value"]}
    parsed_url = urlparse(request_url)
    query_string = parse_qs(parsed_url.query)
    print("URL Query string: ", json.dumps(query_string), flush=True)    


    # read the database credentials from the function configuration 
    ordsbaseurl = dbuser = dbpwd = dbuser_ocid = dbpwd_ocid = ""
    try:
        cfg = ctx.Config()
        ords_base_url = cfg["ORDS_BASE_URL"]
        dbuser_ocid = cfg["DB_USER_SECRET_OCID"]
        dbpwd_ocid = cfg["DB_PASSWORD_SECRET_OCID"]
    except Exception:
        print('Missing function parameters: ords-base-url, db-user and db-pwd', flush=True)
        raise
    
    # Read the db credential secrets from the OCI 
    dbuser = read_secret_value(dbuser_ocid)
    dbpwd = read_secret_value(dbpwd_ocid)
    sql_query_string = get_sql_query(request_url_string, query_string, dbuser)


    result = ords_run_sql(ords_base_url, dbuser, dbpwd, sql_query_string)

    return response.Response(
        ctx, 
        response_data=json.dumps(result),
        headers={"Content-Type": "application/json"}
    )
