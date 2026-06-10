import { Router } from "express";
import { Resource } from "../models/Resource.js";

const router = Router();

router.get("/", async (_req, res) => {
  const resources = await Resource.find().sort({ module: 1, title: 1 });
  res.json(resources);
});

export default router;
