const fs = require("fs");
const axios = require("axios");
const FormData = require("form-data");
const { ML_SERVICE_URL } = require("../config/env");

async function predictWithMl({
  endpoint,
  source,
  image,
  filePath,
  filename,
  contentType,
}) {
  const url = `${ML_SERVICE_URL.replace(/\/$/, "")}/predict/${endpoint}`;

  if (source === "file" && filePath) {
    const formData = new FormData();
    formData.append("image", fs.createReadStream(filePath), { filename });

    const response = await axios.post(url, formData, {
      headers: formData.getHeaders ? formData.getHeaders() : undefined,
      timeout: 120000,
    });

    return response.data;
  }

  if (source === "base64" && image) {
    const response = await axios.post(
      url,
      {
        image,
        filename,
        contentType,
      },
      {
        timeout: 120000,
      },
    );

    return response.data;
  }

  throw new Error("No valid image input provided.");
}

module.exports = {
  predictWithMl,
};
