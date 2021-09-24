var uuid = require('uuid');

function decodeBase64Image(data) {
  var response = {}
  response.data = Buffer.from(data, 'base64');
  return response;
}

module.exports = async function (context, req) {

  try {
    let response = decodeBase64Image(req.body.data);
    const { BlobServiceClient } = require('@azure/storage-blob');
    const blobServiceClient = BlobServiceClient.fromConnectionString(process.env.storageAccount);

    const containerClient = blobServiceClient.getContainerClient(process.env.storageContainer);

    const fileId = uuid.v4();
    const blobName = fileId + req.body.filename;
    const blockBlobClient = containerClient.getBlockBlobClient(blobName);
    const uploadBlobResponse = await blockBlobClient.upload(response.data, response.data.length);



    const Image = require("./models/image.model.js");

    const image = {
      id: fileId,
      name: blobName,
      filetype: req.body.filetype,
      created: Date()
    };

    await Image.create(image);
    context.res.status(200);

  } catch (err) {
    console.log(err.message);
    context.res.status(500);
  }

}
