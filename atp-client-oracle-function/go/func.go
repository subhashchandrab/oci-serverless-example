package main

import (
	"bytes"
	"context"
	b64 "encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"

	fdk "github.com/fnproject/fdk-go"

	"github.com/oracle/oci-go-sdk/v50/common"
	"github.com/oracle/oci-go-sdk/v50/common/auth"
	"github.com/oracle/oci-go-sdk/v50/secrets"
)

type FnConfig struct {
	ordsBaseUrl string
	dbUserOcid  string
	dbPwdOcid   string
	dbUser      string
	dbPwd       string
}

var functionConfig *FnConfig
var secretsClient secrets.SecretsClient

func main() {
	fdk.Handle(fdk.HandlerFunc(myHandler))
}

func myHandler(ctx context.Context, in io.Reader, out io.Writer) {
	log.Print("Inside Go HTTP function for accessing ATP database")

	httpContext, ok := fdk.GetContext(ctx).(fdk.HTTPContext)

	if !ok {
		fdk.WriteStatus(out, 400)
		fdk.SetHeader(out, "Content-Type", "application/json")
		io.WriteString(out, `{"error":"function not invoked via http trigger"}`)
		return
	}
	if functionConfig == nil {
		functionConfig = new(FnConfig)
		// fnContext := httpContext.Context

		functionConfig.ordsBaseUrl = httpContext.Config()["ORDS_BASE_URL"]
		functionConfig.dbUserOcid = httpContext.Config()["DB_USER_SECRET_OCID"]
		functionConfig.dbPwdOcid = httpContext.Config()["DB_PASSWORD_SECRET_OCID"]
		initializeSecretsClient()
		functionConfig.dbUser = readSecretValue(functionConfig.dbUserOcid)
		functionConfig.dbPwd = readSecretValue(functionConfig.dbPwdOcid)
		log.Print("Read the configuration", functionConfig.ordsBaseUrl, functionConfig.dbUser, functionConfig.dbPwd)
	}

	contentType := httpContext.Header().Get("Content-Type")
	log.Print("contentType = ", contentType)
	requestURLString := httpContext.RequestURL()
	log.Print("requestURL = ", requestURLString)
	requestMethod := httpContext.RequestMethod()
	log.Print("requestMethod = ", requestMethod)

	requestUrl, err := url.Parse(requestURLString)
	if err != nil {
		panic(err)
	}

	sqlQueryResult := invokeOrds(getSqlQuery(requestUrl))

	// you can write your own headers & status, if you'd like to
	fdk.SetHeader(out, "Content-Type", "application/json")

	json.NewEncoder(out).Encode(&sqlQueryResult)
}

func getSqlQuery(requestURL *url.URL) string {
	tableName := functionConfig.dbUser + ".products"
	var sqlQuery string = "select name, count from " + tableName
	log.Print("URL Path: ", requestURL.Path)
	queryParams, err := url.ParseQuery(requestURL.RawQuery)
	if err != nil {
		panic(err)
	}
	productName := ""
	productCount := ""

	if val, ok := queryParams["name"]; ok {
		productName = val[0]
	}
	if val, ok := queryParams["count"]; ok {
		productCount = val[0]
	}
	if strings.HasPrefix(requestURL.Path, "/getProducts") {
		sqlQuery = "select name, count from " + tableName
	} else if strings.HasPrefix(requestURL.Path, "/addProduct") {
		sqlQuery = "insert into " + tableName + " values ('" + productName + "' , " + productCount + ")"

	} else if strings.HasPrefix(requestURL.Path, "/updateProduct") {
		sqlQuery = "update " + tableName + " set count=" + productCount + " where name = '" + productName + "'"

	} else if strings.HasPrefix(requestURL.Path, "/deleteProduct") {
		sqlQuery = "delete from " + tableName + " where name = '" + productName + "'"
	}
	return sqlQuery
}

func initializeSecretsClient() {
	resourcePrincipalVersion := os.Getenv("OCI_RESOURCE_PRINCIPAL_VERSION")
	if resourcePrincipalVersion != "" {
		rp, err := auth.ResourcePrincipalConfigurationProvider()
		if err != nil {
			panic(err)
		}
		secretsClient, err = secrets.NewSecretsClientWithConfigurationProvider(rp)
		if err != nil {
			panic(err)
		}
	}
}

func readSecretValue(secretOcid string) string {
	req := secrets.GetSecretBundleRequest{

		SecretId: common.String(secretOcid),
		Stage:    secrets.GetSecretBundleStageCurrent}

	secretResponse, err := secretsClient.GetSecretBundle(context.Background(), req)
	if err != nil {
		panic(err)
	}
	secretBundleContent := secretResponse.SecretBundle.SecretBundleContent
	base64SecretContent := secretBundleContent.(secrets.Base64SecretBundleContentDetails)
	secretContent, _ := b64.StdEncoding.DecodeString(*base64SecretContent.Content)
	return string(secretContent)
}

func invokeOrds(sqlQuery string) map[string]interface{} {
	ordsEndPoint := functionConfig.ordsBaseUrl + functionConfig.dbUser + "/_/sql"
	client := &http.Client{}
	var sqlbytes = []byte(sqlQuery)

	req, err := http.NewRequest(http.MethodPost, ordsEndPoint, bytes.NewBuffer(sqlbytes))
	if err != nil {
		fmt.Print(err.Error())
	}
	req.Header.Add("Accept", "application/json")
	req.Header.Add("Content-Type", "application/sql")
	req.SetBasicAuth(functionConfig.dbUser, functionConfig.dbPwd)
	resp, err := client.Do(req)
	if err != nil {
		fmt.Print(err.Error())
	}
	log.Print("Status code: ", resp.StatusCode)
	var sqlQueryResult = make(map[string]interface{})
	if resp.StatusCode == 200 {
		defer resp.Body.Close()
		bodyBytes, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			fmt.Print(err.Error())
		}
		var ordsRestResult map[string]interface{}
		json.Unmarshal(bodyBytes, &ordsRestResult)

		for _, resultJsonRecord := range ordsRestResult {
			if resultJsonRecord, ok := resultJsonRecord.([]interface{}); ok {
				for _, resultJsonItem := range resultJsonRecord {
					if resultJsonItem, ok := resultJsonItem.(map[string]interface{}); ok {
						if val, ok := resultJsonItem["statementText"]; ok {
							sqlQueryResult["sql_statement"] = val
						}
						if val, ok := resultJsonItem["errorDetails"]; ok {
							sqlQueryResult["error"] = val
						}
						if val, ok := resultJsonItem["resultSet"]; ok {
							if resultSet, ok := val.(map[string]interface{}); ok {
								if resultSetItem, ok := resultSet["items"]; ok {
									sqlQueryResult["results"] = resultSetItem
								}
							}
						}
						if val, ok := resultJsonItem["response"]; ok {
							sqlQueryResult["response"] = val
						}
					}

				}
			}
		}

	} else {
		log.Print("ORDS Rest API returned error")
	}
	return sqlQueryResult
}
