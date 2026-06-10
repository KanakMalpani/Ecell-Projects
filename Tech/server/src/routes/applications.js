import { Router } from "express";
import { Application } from "../models/Application.js";

const router = Router();

router.get("/", async (_req, res) => {
  const applications = await Application.find().sort({ createdAt: -1 });
  res.json(applications);
});

router.post("/", async (req, res) => {
  const { name, email, domain, message } = req.body;
  if (!name || !email || !domain) {
    return res.status(400).json({ error: "name, email, and domain are required" });
  }

  const application = await Application.create({ name, email, domain, message });
  res.status(201).json(application);
});

export default router;
