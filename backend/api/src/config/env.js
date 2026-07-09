const path = require("path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

module.exports = {
  PORT: process.env.PORT || 3000,
  ML_SERVICE_URL:
    process.env.ML_SERVICE_URL ||
    process.env.FASTAPI_URL ||
    "http://localhost:8000",
};
