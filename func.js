const fdk=require('@fnproject/fdk');
const oracledb = require('oracledb');
const dbconfig = require('./dbconfig.js');

fdk.handle(async function(input){

  
  console.log('\nThis is a OCI Functions for demonstrating provisioned concurrency..')
  console.log(input);
  if (input) {
	//TODO to implement product specific operation like create,delete and update
    return '{ input received : ' + input + '}' 
  }else{
    return getdb()
  }
})

async function getdb(){
  let result = '';
  //console.log(process.env.CONNECT_STRING, process.env.DB_USER);
  try {
    connection =  await oracledb.getConnection(dbconfig);
    result =  await connection.execute(
    `SELECT brand, title, description
     FROM test_user.products`
    );
   
    for(let results in result.rows){
      const [brand,title,description] = result.rows[results];
      //console.log(brand,title,description);
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

