import mongoose from "mongoose";

const applicationSchema = new mongoose.Schema(
  {
    name: { type: String, required: true, trim: true },
    email: { type: String, required: true, trim: true, lowercase: true },
    domain: {
      type: String,
      enum: ["tech", "ai", "design", "marketing"],
      required: true,
    },
    message: { type: String, default: "" },
  },
  { timestamps: true }
);

export const Application = mongoose.model("Application", applicationSchema);
