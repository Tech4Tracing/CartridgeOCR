async function create (newImage) {
  const dbContext = require("../data/databaseContext.js");
  const container = await dbContext.create();
  await container.items.create(newImage);
};

module.exports.create = create;
