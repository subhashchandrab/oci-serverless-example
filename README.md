# OCI Serverless functions
Serverless is a cloud-native development model that allows developers to build and run applications without having to manage servers. Oracle Cloud Functions is a serverless platform that lets developers create, run, and scale applications without managing any infrastructure. 

In the current use case, we will explore how we can use Oracle Cloud Functions as backend for any web based applications to build the serverless applications.

## OCI Serverless functions as application backend
![oci-serverless-demo](https://user-images.githubusercontent.com/22868753/132651086-3d3f76a1-1d88-424b-bad3-2685428722fc.png)



## Summary
We have a static web page based on plain html with all required javascript/css embedded inside it. This page contains the UI to handle a generic product store which contains various products and their availability(count of available items for each product). The UI contains the following operations
- Fetch all products
- Add a new product to the store
- Update count of an existing product
- Delete an existing product from the store


We need to setup the following OCI components

## ATP Database

* Create an [Autonomous Transaction Processing (ATP) Database](https://docs.oracle.com/en-us/iaas/Content/Database/Tasks/adbcreating.htm)
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
 
## OCI Functions
* Upgrade to the [latest fn CLI](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsupgradingfncli.htm)
* Create a [Functions Application](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsquickstartcloudshell.htm) with a name 'serverless-demo'
* Add the following configuration parameters to the application
![function-app-configuration](https://user-images.githubusercontent.com/22868753/134468231-20cf7eb1-004b-488f-934a-afff9f9987c6.jpg)

1. ORDS_BASE_URL : The URL we copied in the steps mentioned in previous section on ATP Database. 
2. CONNECT_STRING : Connect string name will be available in tnsnames.ora file(Can be found in the downloaded wallet folder of the ATP). Use the name of the format ATPName_TP
3. DB_USER & DB_PASSWORD : Use the values as shown in the above screen shot as we have used the same credentials in the SQL script we executed in the previous section.

* Clone the github repository:
```
$git clone https://github.com/subhashchandrab/oci-serverless-example.git 
$cd atp-client-python-function
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





