# OCI Serverless functions
Serverless is a cloud-native development model that allows developers to build and run applications without having to manage servers. Oracle Cloud Functions is a serverless platform that lets developers create, run, and scale applications without managing any infrastructure. 

In the current use case, we will explore how we can use Oracle Cloud Functions as backend in the API Gateway so that they can be consumed by any web based applications to build the serverless applications.

## OCI Serverless functions as application backend
The following OCI components are used in the current usecase
- [Autonomous Transaction Processing](https://docs.oracle.com/en/cloud/paas/atp-cloud/index.html)
- [Vault](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm)
- [Oracle Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
- [API Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm)

![oci-serverless-example](https://user-images.githubusercontent.com/22868753/134862156-bda0dc9a-058c-4631-9e5e-5ddb60f87f9f.png)



## Summary
We have a static web page based on plain html with all required javascript/css embedded inside it. This page contains the UI to handle a generic product store which contains various products and their availability(count of available items for each product).  The UI contains the following operations
- Fetch all products
- Add a new product to the store
- Update count of an existing product
- Delete an existing product from the store

The product data is maintained in ATP database.  When this UI is accessed using any of the above operations, it invokes the respective OCI API Gateway endpoint URL using REST call. API Gateway is responsible for invoking the Oracle function mapped to the path invoked by the application. This Oracle Function is responsible for interacting with ATP to perform all the required CRUD operations.

We need to setup the following OCI components. 

## ATP Database

* Create an [Autonomous Transaction Processing (ATP) Database](https://www.oracle.com/webfolder/technetwork/tutorials/obe/cloud/atp/obe_provisioning%20autonomous%20transaction%20processing/provisioning_autonomous_transaction_processing.html)
* From the ATP details page, click on DB Connection -> Instance Wallet -> Download Wallet. Extract the contents to any folder. You need to refer the tnsnames.ora file in the  next section
* Access the ATP Service Console. In the Home page, make a note of the ORDS base URL by clicking on Copy URL under RESTful Services and SODA section.
* Click on Database Actions to open the SQL Developer Web. Clik on SQL to open the SQL worksheet and execute the following queries

```
/* Create a user 'test_user' for connecting to the ATP from the application */
CREATE USER test_user IDENTIFIED BY default_Password1;

/* Grant all necessary permission for the tes_user created above */
GRANT CREATE SESSION TO test_user;
GRANT UNLIMITED TABLESPACE TO test_user;

/* Create a separate role 'test_role' and grant it to the above user */
CREATE ROLE test_role;
GRANT test_role TO test_user;
 
 /* Create a table for storing the product information. We are storing only 2 details namely product name and product count */
CREATE TABLE test_user.products (
name VARCHAR2(20),
count NUMBER
);
 
/* Grant relevant permissions for the test_role created above */  
GRANT SELECT, INSERT, UPDATE, DELETE ON test_user.products TO test_role;
 
/* Prepare some sample product data for testing the application */ 
INSERT INTO test_user.products VALUES ('Pen',100);
INSERT INTO test_user.products VALUES ('Pencil',200);
INSERT INTO test_user.products VALUES ('Notebook',50);
INSERT INTO test_user.products VALUES ('Sketch pen',80);
INSERT INTO test_user.products VALUES ('Eraser',150);

/* Verify the inserted product data  */
select name, count from test_user.products;
```

* From Global Action Menu, select Administration -> Database Users. Select the TEST_USER and click on Enable REST
 ![rest-enable-atp-user](https://user-images.githubusercontent.com/22868753/134461040-203a4326-8fea-4deb-ad0a-8b564c72a12f.jpg)
 
## OCI Vault for storing Database Credentials
[Vaults](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) securely store master encryption keys and secrets to pass the sensitive information to the application. In the current usecase, we will use the Vault to create the secrets for the ATP database username and password.
* Create a [Vault](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingvaults.htm).
   ![CreateVault](https://user-images.githubusercontent.com/22868753/139017788-a2beeeff-8f2d-434b-9a97-592e110dd0d8.jpg)
  Make sure that you don't click on the check box for Virutal Private Vault as this is only demo
* Go to the Vault details page and select **Master Encryption Keys** from the Resources. Now click on the Create Key
* Enter the required information and click on Create Key. Select the Protection mode as the Software
 ![CreateKey](https://user-images.githubusercontent.com/22868753/139019311-f1c87233-c57e-4825-9984-3491e6cfac27.jpg)
* Select **Secrets** and click on Create Secret. This secret is meant for storing the ATP database user ID. Fill the required information. For Encryption Key, select the key created in the previous step. Give test_user as the content and click Create Secret.
* Simliary create a secret for storing the ATP database password
* Make a note of the OCID for both the secrets created above.

## OCI Functions
* Upgrade to the [latest fn CLI](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsupgradingfncli.htm)
* Create a [Functions Application](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsquickstartcloudshell.htm) with a name 'serverless-demo'
* Add the following configuration parameters to the application

1. ORDS_BASE_URL : The URL we copied in the steps mentioned in the section on ATP Database. 
2. DB_USER_SECRET_OCID : The OCID of the ATP DB User ID secret created in the previous section
3. DB_PASSWORD_SECRET_OCID : The OCID of the ATP DB password secret created in the previous section

* Clone the github repository:
```
$git clone https://github.com/subhashchandrab/oci-serverless-example.git 
$cd atp-client-java-function
```

* Setup your environment for pushing the function image to the OCI repository. Please refer [OCI Fn quickstart](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsquickstartlocalhost.htm) for help.

* After logging in to the OCI registry, execute the following command to verify that the function application created above(serverless-demo) is listed
```
$fn list apps
NAME		ID	
serverless-demo	ocid1.fnapp.oc1.phx.aaaa.....
```

* Deploy the function into the application
```
$fn -v deploy --app serverless-demo
```

* From OCI Console, click Developer Services -> Functions -> Application -> serverless-demo. Verify that the function named product-store-operations-java is shown in the list of functions.

## OCI API Gateway
* Create an [API Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm)
* Create a deployment named **product-store** with CORS configuration as shown below
![create-apigw-basicinfo](https://user-images.githubusercontent.com/22868753/134850884-f0a5817d-5233-4d5d-ba91-5eb445f10c58.jpg)

![apigw-cors-config](https://user-images.githubusercontent.com/22868753/134850923-44975138-7cf2-49b9-a0fd-194a39c999ce.jpg)

* Click Next and create a Route for the path **/getProducts** as shown below. Type should be selected as **Oracle Functions** and the application and function should be selected by referring to the function deployed in earlier section.
![function-app-configuration](https://user-images.githubusercontent.com/22868753/134851345-03976609-c89a-412b-b437-64bfdb27517d.jpg)

* Similar to the above step, create the following routes

|      PATH      | METHODS | TYPE             | APPLICATION     | FUNCTION NAME            |
|:--------------:|---------|------------------|-----------------|--------------------------|
| /addProduct    | PUT     | Oracle Functions | serverless-demo | product-store-operations |
| /updateProduct | PUT     | Oracle Functions | serverless-demo | product-store-operations |
| /deleteProduct | PUT     | Oracle Functions | serverless-demo | product-store-operations |

* Click Next and click Create

* Go to Deployment Details page and copy the Endpoint URL.
![apigw-dep-endpoint-url](https://user-images.githubusercontent.com/22868753/134852732-e188257d-a01d-4cfe-9d51-096c07d0afcb.jpg)

## Setup HTML UI
* Go to the git cloned repository above.
```
$cd front-end/html
$vi index.html
```
* Locate the following line and update the apiEndpointUrl with the URL copied above(from API Gateway Deployment Details page)
```
var apiEndpointUrl = "https://*******.apigateway.*****.oci.customer-oci.com";//Replace the API Gateway endpoint URL here
```
* Save the file

## Object Storage setup to access HTML UI
* Create a standard type [object storage bucket](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/managingbuckets.htm) with all default settings
* Upload the index.html(Updated index.html from previous section) file into the bucket.
* Create a Pre-Authenticated Request for the uploaded file and note down the URL 
![create-objectstorage-par](https://user-images.githubusercontent.com/22868753/134857990-7edbdb01-521b-411b-8886-76d284084c8d.jpg)


## Update the API Gateway deployment
* Go to the Deployment Details page for the API deployment created earlier. Add the following route and update the URL with the URL copied in the previous step
![apigw-index-route](https://user-images.githubusercontent.com/22868753/134857524-6a02fa78-52f8-41a4-9bfb-2e452fc8816f.jpg)

## Access the UI
* Copy the API Gateway deployment endpoint URL and paste it in a browser. You should see the following operations. Perform the operations like Add Product, Delete Product and Update Product
![product-store-html-ui](https://user-images.githubusercontent.com/22868753/134859179-4dffefd2-09b8-4c97-979a-ba27914b82a5.jpg)

## Conclusion
We verified how a web application can access API Gateway endpoint which has Oracle Function (which accesses ATP) as the backend.
