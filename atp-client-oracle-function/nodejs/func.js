const fdk=require('@fnproject/fdk');
const common = require('oci-common');
const axios = require('axios');
const secrets = require('oci-secrets');
const url = require('url');

const readSecret = async (secretOcid) => {
  var secretContent = "";
  const provider = await common.ResourcePrincipalAuthenticationDetailsProvider.builder();
  const secretsClient = await new secrets.SecretsClient({authenticationDetailsProvider:provider});
  const getSecretBundleRequest = {
      secretId: secretOcid,
      stage: secrets.requests.GetSecretBundleByNameRequest.Stage.Current
    };

    const secretBundleResponse = await secretsClient.getSecretBundle(
      getSecretBundleRequest
    ); 
    secretContent = secretBundleResponse.secretBundle.secretBundleContent.content;
    return Buffer.from(secretContent, 'base64').toString('ascii');
};

const loadConfiguration = async (ctx) => {
  let fnConfig = {};
  fnConfig['ordsBaseUrl'] = ctx.config["ORDS_BASE_URL"];
  var dbUserOcid = ctx.config["DB_USER_SECRET_OCID"];
  var dbPwdOcid = ctx.config["DB_PASSWORD_SECRET_OCID"];
  

  fnConfig['dbUser']  = await readSecret(dbUserOcid);
  fnConfig['dbPwd'] = await readSecret(dbPwdOcid);
  return fnConfig;
};

const getSqlQuery = (fnConfig, ctx) => {
  let tableName = fnConfig['dbUser'] + ".products";
  let sqlQuery = "select name, count from " + tableName;
  let path = '';
  let httpCtx = ctx.httpGateway;
  let queryParams = {};
  if(httpCtx){
    let requestUrlString = httpCtx.requestURL;
    console.log("Request URL" , httpCtx.requestURL);
    if(requestUrlString){
      let reqUrl = url.parse(requestUrlString,true);
      path = reqUrl.pathname;
      queryParams = reqUrl.query;
    }
    else{
      console.log("Request URL not available. Will use /getProducts as the default path.");
    }
  }
  if (path.startsWith("/getProducts")){
    sqlQuery = "select name, count from " + tableName;
  }
  else if (path.startsWith("/addProduct")) {
    product_name = queryParams['name'];
    product_count = queryParams['count'];
    sqlQuery = "insert into "+ tableName + " values ('" + product_name +"' , "+ product_count + ")";
  }
  else if (path.startsWith("/updateProduct")) {
      product_name = queryParams['name'];
      product_count = queryParams['count'];;
      sqlQuery = "update "+ tableName +" set count=" + product_count + " where name = '"+product_name+"'";
  }
  else if (path.startsWith("/deleteProduct")) {
      product_name = queryParams['name'];
      sqlQuery = "delete from "+ tableName + " where name = '"+product_name+"'" ;
  }
  return sqlQuery; 
}

const invokeOrds = async (fnConfig, sqlQuery) => {
  var ordsBaseUrl = fnConfig['ordsBaseUrl'];
  var dbUser = fnConfig['dbUser'];
  var dbPwd = fnConfig['dbPwd'];
  console.log("Invoking the ords API.. "+ ordsBaseUrl + dbUser + '/_/sql');
  let result = {};
  let res = await axios({
    method: 'post',
    url: ordsBaseUrl + dbUser + '/_/sql',
    auth: {
        username: dbUser,
        password: dbPwd
    },
    headers: {
        'Content-Type': 'application/sql',
    },          
    data: sqlQuery

  });

  var resultItem = res.data.items[0];
  result["sql_statement"] = resultItem["statementText"];
  if( "errorDetails" in resultItem ){
    result["error"] = resultItem["errorDetails"];
  }
  if( "response" in resultItem ){
    result["response"] = resultItem["response"];
  }   
  if( "resultSet" in resultItem ){
    result["results"] = resultItem["resultSet"]["items"];
    result["count"] = resultItem["resultSet"]["count"];
  }
  console.log(`statusCode: ${res.status}`);
 
   return result
}

const handleFunction = async (input, ctx) => {
  console.log('input: ' + input)
  let fnConfig = await loadConfiguration(ctx);
  let sqlQuery = getSqlQuery(fnConfig, ctx);
  let resultJson = await invokeOrds(fnConfig, sqlQuery);
  ctx.responseContentType = 'application/json';
  var jsonResultStr = JSON.stringify(resultJson);
  // console.log("Return result: " + jsonResultStr);
  return resultJson;
}

fdk.handle(handleFunction);
