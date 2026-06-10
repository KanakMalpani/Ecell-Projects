import mongoose from "mongoose";

const resourceSchema = new mongoose.Schema(
  {
    module: { type: Number, required: true },
    title: { type: String, required: true },
    type: { type: String, enum: ["reading", "video", "practice"], required: true },
    url: { type: String, required: true },
    description: { type: String, default: "" },
  },
  { timestamps: true }
);

export const Resource = mongoose.model("Resource", resourceSchema);
