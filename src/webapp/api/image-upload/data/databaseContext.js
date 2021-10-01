const CosmosClient = require("@azure/cosmos").CosmosClient;

/*
// This script ensures that the database is setup and populated correctly
*/
async function create() {

  const client = new CosmosClient({ endpoint: process.env.cosmosEndpoint, key: process.env.cosmosKey });
  const partitionKey = process.env.cosmosPartitionKey;

  /**
   * Create the database if it does not exist
   */
  const { database } = await client.databases.createIfNotExists({
    id: process.env.cosmosDatabaseId
  });
  console.log(`Created database:\n${database.id}\n`);

  /**
   * Create the container if it does not exist
   */
  const { container } = await client
    .database(process.env.cosmosDatabaseId)
    .containers.createIfNotExists(
      { id: process.env.cosmosContainerId, key: process.env.cosmosPartitionKey },
      { offerThroughput: 400 }
    );

  console.log(`Created container:\n${container.id}\n`);


  //const database = client.database(process.env.cosmosDatabaseId);
  //const container = database.container(process.env.cosmosContainerId);
  return container;
}

module.exports.create = create;
