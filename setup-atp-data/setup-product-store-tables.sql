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
