const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export interface PredictionResponse {
  prediction: number;
  confidence: number;
}

async function parsePredictionResponse(response: Response): Promise<PredictionResponse> {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data?.message || "Prediction request failed");
  }

  const payload = data?.prediction ?? data;

  if (typeof payload?.prediction === "number" && typeof payload?.confidence === "number") {
    return payload;
  }

  throw new Error("Unexpected prediction response from API");
}

export async function predictFromImage(file: File): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append("image", file, file.name);

  const response = await fetch(`${API_BASE_URL}/predict/image`, {
    method: "POST",
    body: formData,
  });

  return parsePredictionResponse(response);
}

export async function predictFromDrawing(dataUrl: string): Promise<PredictionResponse> {
  const response = await fetch(dataUrl);
  const blob = await response.blob();
  const formData = new FormData();
  formData.append("image", blob, "drawing.png");

  const predictionResponse = await fetch(`${API_BASE_URL}/predict/drawing`, {
    method: "POST",
    body: formData,
  });

  return parsePredictionResponse(predictionResponse);
}
