#
# oci-serverless-demo-python version 1.0.
# This function connects to the ATP database and performs the basic operations
# like Fetch/Create/Update/Delete for the products table

import io
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
def getSqlQuery(requestUrlString, queryString, dbUser):
    tableName = dbUser + ".products"
    sqlQuery = "select name, count from" + tableName
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

def handler(ctx, data: io.BytesIO=None):
    # retrieving the request headers
    #headers = ctx.Headers()
    #print("Headers:",  json.dumps(headers)) 

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
    requesturl = ctx.RequestURL()
    requestUrlString = json.dumps(requesturl)
    print("Request URL: ", requestUrlString, flush=True)
    
    # retrieving query string from the request URL, e.g. {"param1":["value"]}
    parsed_url = urlparse(requesturl)
    query_string = parse_qs(parsed_url.query)
    print("URL Query string: ", json.dumps(query_string), flush=True)    


    # read the database properties from the function configuration 
    ordsbaseurl = dbuser = dbpwdcypher = dbpwd = ""
    try:
        cfg = ctx.Config()
        ordsbaseurl = cfg["ORDS_BASE_URL"]
        dbuser = cfg["DB_USER"]
        dbpwdcypher = cfg["DB_PASSWORD"]
        dbpwd = dbpwdcypher  # The decryption of the db password using OCI KMS would have to be done, however it is addressed here
    except Exception:
        print('Missing function parameters: ords-base-url, db-user and db-pwd', flush=True)
        raise

    
    sqlQueryString = getSqlQuery(requestUrlString, query_string, dbuser)
    print("SQL query string:", sqlQueryString)

    result = ords_run_sql(ordsbaseurl, dbuser, dbpwd, sqlQueryString)

    return response.Response(
        ctx, 
        response_data=json.dumps(result),
        headers={"Content-Type": "application/json"}
    )
