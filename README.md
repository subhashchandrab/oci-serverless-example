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
* Click on OCI Console -> Autonomous Database -> DB Connection and download the wallet.
* Access the ATP Service Console -> SQL Developer Web and perform the following actions:

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

* Go to Administration -> DATABASE USERS. Select the TEST_USER and click on Enable REST
 ![rest-enable-atp-user](https://user-images.githubusercontent.com/22868753/134461040-203a4326-8fea-4deb-ad0a-8b564c72a12f.jpg)

