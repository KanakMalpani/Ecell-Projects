import { Router } from "express";
import { Event } from "../models/Event.js";

const router = Router();

router.get("/", async (_req, res) => {
  const events = await Event.find().sort({ date: 1 });
  res.json(events);
});

router.post("/", async (req, res) => {
  const { title, description, date, domain, location } = req.body;
  if (!title || !description || !date) {
    return res.status(400).json({ error: "title, description, and date are required" });
  }

  const event = await Event.create({ title, description, date, domain, location });
  res.status(201).json(event);
});

export default router;
