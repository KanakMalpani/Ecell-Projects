import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import mongoose from "mongoose";
import applicationsRouter from "./routes/applications.js";
import eventsRouter from "./routes/events.js";
import resourcesRouter from "./routes/resources.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const CLIENT_ORIGIN = process.env.CLIENT_ORIGIN || "http://localhost:5173";
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/ecell-tech";

app.use(cors({ origin: CLIENT_ORIGIN }));
app.use(express.json());

app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "E-Cell Tech API",
    database: mongoose.connection.readyState === 1 ? "connected" : "disconnected",
  });
});

app.use("/api/events", eventsRouter);
app.use("/api/applications", applicationsRouter);
app.use("/api/resources", resourcesRouter);

async function start() {
  try {
    await mongoose.connect(MONGODB_URI);
    console.log("MongoDB connected");
  } catch (error) {
    console.warn("MongoDB unavailable. API will run but database routes may fail.");
    console.warn(error.message);
  }

  app.listen(PORT, () => {
    console.log(`E-Cell Tech API running on http://localhost:${PORT}`);
  });
}

start();
