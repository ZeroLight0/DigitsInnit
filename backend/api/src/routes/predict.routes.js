const express = require("express");

const upload = require("../../uploads/upload.middleware");
const {
  predictImage,
  predictDrawing,
  healthCheck,
} = require("../controllers/predict.controller");

const router = express.Router();

router.post("/predict/image", upload.single("image"), predictImage);
router.post("/predict/drawing", upload.single("image"), predictDrawing);
router.get("/health", healthCheck);

module.exports = router;
