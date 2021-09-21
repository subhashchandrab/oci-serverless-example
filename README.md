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


