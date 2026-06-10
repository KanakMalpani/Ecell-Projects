import dotenv from "dotenv";
import mongoose from "mongoose";
import { Event } from "./models/Event.js";
import { Resource } from "./models/Resource.js";

dotenv.config();

const events = [
  {
    title: "MERN Stack Bootcamp",
    description: "Hands-on session covering React, Express, and MongoDB integration.",
    date: "2026-07-15",
    domain: "tech",
    location: "Innovation Hub",
  },
  {
    title: "ML Pipeline Workshop",
    description: "Build and evaluate a document intelligence pipeline end to end.",
    date: "2026-07-22",
    domain: "ai",
    location: "CS Lab 3",
  },
  {
    title: "Founder Pitch Night",
    description: "Student startups pitch to mentors and alumni investors.",
    date: "2026-08-05",
    domain: "all",
    location: "Main Auditorium",
  },
];

const resources = [
  {
    module: 1,
    title: "W3Schools HTML Intro",
    type: "reading",
    url: "https://www.w3schools.com/html/html_intro.asp",
    description: "Beginner-friendly HTML fundamentals.",
  },
  {
    module: 2,
    title: "W3Schools CSS Intro",
    type: "reading",
    url: "https://www.w3schools.com/css/css_intro.asp",
    description: "Core CSS concepts and examples.",
  },
  {
    module: 2,
    title: "Flexbox Froggy",
    type: "practice",
    url: "https://flexboxfroggy.com/",
    description: "Interactive Flexbox practice game.",
  },
  {
    module: 2,
    title: "CSS Grid Garden",
    type: "practice",
    url: "https://cssgridgarden.com/",
    description: "Interactive CSS Grid practice game.",
  },
  {
    module: 3,
    title: "JavaScript.info",
    type: "reading",
    url: "https://javascript.info/",
    description: "In-depth JavaScript learning resource.",
  },
  {
    module: 3,
    title: "Namaste JavaScript",
    type: "video",
    url: "https://www.youtube.com/playlist?list=PLlasXeu85E9cQ32gLCvAvr9vNaUccPVNP",
    description: "Deep dive into how JavaScript works.",
  },
  {
    module: 4,
    title: "React Official Docs",
    type: "reading",
    url: "https://react.dev/learn",
    description: "Official React learning path.",
  },
  {
    module: 5,
    title: "Node.js & Express Tutorial",
    type: "video",
    url: "https://www.youtube.com/playlist?list=PLCQ35r0Zy6o0tLz9Nq9QzN9iWjK8y9B8x",
    description: "Backend development with Node.js.",
  },
  {
    module: 6,
    title: "MongoDB Getting Started",
    type: "reading",
    url: "https://www.w3schools.com/mongodb/mongodb_get_started.php",
    description: "MongoDB basics and operations.",
  },
  {
    module: 7,
    title: "MERN Stack Overview",
    type: "reading",
    url: "https://www.geeksforgeeks.org/mern/understand-mern-stack/",
    description: "How MERN components fit together.",
  },
  {
    module: 7,
    title: "Full MERN Walkthrough",
    type: "video",
    url: "https://youtu.be/F9gB5b4jgOI",
    description: "End-to-end MERN project demo.",
  },
  {
    module: 8,
    title: "Git & GitHub Intro",
    type: "reading",
    url: "https://www.w3schools.com/git/git_intro.asp",
    description: "Version control and collaboration basics.",
  },
];

async function seed() {
  const uri = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/ecell-tech";
  await mongoose.connect(uri);

  await Event.deleteMany({});
  await Resource.deleteMany({});
  await Event.insertMany(events);
  await Resource.insertMany(resources);

  console.log("Seeded events and learning resources.");
  await mongoose.disconnect();
}

seed().catch((error) => {
  console.error(error);
  process.exit(1);
});
