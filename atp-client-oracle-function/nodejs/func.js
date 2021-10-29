const fdk=require('@fnproject/fdk');
const oracledb = require('oracledb');
const dbconfig = require('./dbconfig.js');

fdk.handle(async function(input){

  
  console.log('This is a OCI Functions for demonstrating provisioned concurrency.')
  console.log(input);
  if (input) {
	//TODO to implement product specific operation like create,delete and update
    return '{ input received : ' + input + '}' 
  }else{
    return getProducts()
  }
})

async function getProducts(){
  let result = '';
  //console.log("Verify that the required environment variables are set as declared in dbconfig.js",process.env.CONNECT_STRING, process.env.DB_USER);
  try {
    connection =  await oracledb.getConnection(dbconfig);
    result =  await connection.execute(`SELECT name, count FROM test_user.products`);
   
    for(let results in result.rows){
      const [name,count] = result.rows[results];
    }
  } catch (err) {
      console.error(err);
    } finally {
      if (connection) {
          try {
            await connection.close();
          } catch (err) {
              console.error(err);
          }
      }
    }
  return result
}
