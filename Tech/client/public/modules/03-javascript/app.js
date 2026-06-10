const events = [
  { title: "MERN Workshop", domain: "tech", date: "2026-07-12" },
  { title: "ML Pipeline Sprint", domain: "ai", date: "2026-07-18" },
  { title: "Brand Sprint", domain: "design", date: "2026-07-22" },
  { title: "Founder AMA", domain: "tech", date: "2026-08-02" },
  { title: "Automation Demo Day", domain: "ai", date: "2026-08-10" },
];

const eventList = document.getElementById("event-list");
const filterButtons = document.querySelectorAll(".filter-btn");
const rsvpCountEl = document.getElementById("rsvp-count");
const rsvpBtn = document.getElementById("rsvp-btn");
const rsvpMessage = document.getElementById("rsvp-message");
const contactForm = document.getElementById("contact-form");
const savedContactsEl = document.getElementById("saved-contacts");

let activeFilter = "all";

function renderEvents() {
  const filtered = events.filter((event) =>
    activeFilter === "all" ? true : event.domain === activeFilter
  );

  eventList.innerHTML = filtered
    .map(
      (event) =>
        `<li><strong>${event.title}</strong><br><span>${event.domain.toUpperCase()} - ${event.date}</span></li>`
    )
    .join("");
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    activeFilter = button.dataset.filter;
    renderEvents();
  });
});

function loadRsvpCount() {
  const count = Number(localStorage.getItem("ecell-rsvp-count") || 0);
  rsvpCountEl.textContent = String(count);
}

rsvpBtn.addEventListener("click", () => {
  const next = Number(localStorage.getItem("ecell-rsvp-count") || 0) + 1;
  localStorage.setItem("ecell-rsvp-count", String(next));
  rsvpCountEl.textContent = String(next);
  rsvpMessage.textContent = "You are registered for Demo Day!";
});

function loadContacts() {
  const contacts = JSON.parse(localStorage.getItem("ecell-contacts") || "[]");
  savedContactsEl.innerHTML = contacts
    .map((contact) => `<li>${contact.name} - ${contact.email}</li>`)
    .join("");
}

contactForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = document.getElementById("contact-name").value.trim();
  const email = document.getElementById("contact-email").value.trim();
  if (!name || !email) return;

  const contacts = JSON.parse(localStorage.getItem("ecell-contacts") || "[]");
  contacts.push({ name, email });
  localStorage.setItem("ecell-contacts", JSON.stringify(contacts));
  contactForm.reset();
  loadContacts();
});

renderEvents();
loadRsvpCount();
loadContacts();
