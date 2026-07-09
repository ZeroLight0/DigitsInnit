const { predictWithMl } = require("../services/ml.service");

function getBase64Image(req) {
  if (req.file?.path) {
    return {
      source: "file",
      filePath: req.file.path,
      filename: req.file.originalname,
    };
  }

  if (typeof req.body?.image === "string" && req.body.image.trim()) {
    return {
      source: "base64",
      image: req.body.image,
      filename: req.body.filename || "image.png",
      contentType: req.body.contentType || "image/png",
    };
  }

  return null;
}

async function predictImage(req, res, next) {
  try {
    const imageInput = getBase64Image(req);

    if (!imageInput) {
      return res
        .status(400)
        .json({
          success: false,
          message: "Please provide an image file or a base64 image.",
        });
    }

    const prediction = await predictWithMl({
      endpoint: "image",
      ...imageInput,
    });

    return res.json({ success: true, prediction });
  } catch (error) {
    return next(error);
  }
}

async function predictDrawing(req, res, next) {
  try {
    const imageInput = getBase64Image(req);

    if (!imageInput) {
      return res
        .status(400)
        .json({
          success: false,
          message: "Please provide a drawing image file or a base64 image.",
        });
    }

    const prediction = await predictWithMl({
      endpoint: "drawing",
      ...imageInput,
    });

    return res.json({ success: true, prediction });
  } catch (error) {
    return next(error);
  }
}

function healthCheck(req, res) {
  return res.json({ success: true, status: "ok" });
}

module.exports = {
  predictImage,
  predictDrawing,
  healthCheck,
};
