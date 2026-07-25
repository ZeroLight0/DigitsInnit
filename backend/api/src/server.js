const app = require("./app");
const { PORT } = require("./config/env");

const port = Number(PORT) || 5000;

app.listen(port, () => {
  console.log(`API server listening on port ${port}`);
});
