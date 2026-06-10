import mongoose from "mongoose";

const eventSchema = new mongoose.Schema(
  {
    title: { type: String, required: true, trim: true },
    description: { type: String, required: true, trim: true },
    date: { type: String, required: true },
    domain: {
      type: String,
      enum: ["tech", "ai", "design", "marketing", "all"],
      default: "all",
    },
    location: { type: String, default: "NIT Trichy Campus" },
  },
  { timestamps: true }
);

export const Event = mongoose.model("Event", eventSchema);
