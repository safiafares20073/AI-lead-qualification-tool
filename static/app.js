"use strict";

const sampleMessage = "Hi, I'm Sara Ahmed from Bright Tech. We need an AI chatbot for our website. Our budget is $5,000, and we want to launch next month. You can reach me at sara@brighttech.example or +1 555 010 1234. Could you send us a proposal?";
const byId = (id) => document.getElementById(id);
const form = byId("lead-form");
const message = byId("lead-message");
const analyzeButton = byId("analyze-button");
const sampleButton = byId("sample-button");
const detailFields = ["name", "company", "email", "phone", "need", "budget", "timeline"];
const textFields = ["category", "intent", "summary", "suggested_reply"];
const expectedFields = [...detailFields, ...textFields, "score", "priority"];
let currentResult = null;

function updateCount() {
  byId("character-count").textContent = `${message.value.length.toLocaleString("en-US")} / 12,000`;
}

function showState(state) {
  for (const name of ["empty-state", "loading-state", "error-state", "results"]) {
    byId(name).hidden = name !== state;
  }
}

function validResult(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) return false;
  if (Object.keys(data).length !== expectedFields.length || !expectedFields.every((field) => Object.hasOwn(data, field))) return false;
  if (!detailFields.every((field) => data[field] === null || (typeof data[field] === "string" && data[field].trim()))) return false;
  if (!textFields.every((field) => typeof data[field] === "string" && data[field].trim())) return false;
  if (!Number.isInteger(data.score) || data.score < 0 || data.score > 100) return false;
  return data.priority === (data.score < 40 ? "low" : data.score < 70 ? "medium" : "high");
}

function renderResult(data) {
  for (const field of [...detailFields, ...textFields, "score"]) {
    byId(field).textContent = data[field] === null ? "Not provided" : String(data[field]);
  }
  byId("priority").textContent = `${data.priority[0].toUpperCase()}${data.priority.slice(1)} priority`;
  byId("priority").className = `priority ${data.priority}`;
  byId("json-output").textContent = JSON.stringify(data, null, 2);
  byId("copy-status").textContent = "";
  currentResult = data;
  showState("results");
}

// This button only edits local text. It never submits the form or calls fetch.
sampleButton.addEventListener("click", () => {
  message.value = sampleMessage;
  updateCount();
  message.focus();
});
message.addEventListener("input", updateCount);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (analyzeButton.disabled) return;
  const inquiry = message.value.trim();
  if (!inquiry) {
    byId("error-message").textContent = "Paste a lead message before analyzing.";
    showState("error-state");
    message.focus();
    return;
  }
  currentResult = null;
  analyzeButton.disabled = true;
  sampleButton.disabled = true;
  message.disabled = true;
  byId("button-label").textContent = "Analyzing…";
  byId("analysis-panel").setAttribute("aria-busy", "true");
  showState("loading-state");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 65000);
  try {
    const response = await fetch("/qualify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: inquiry }),
      signal: controller.signal,
    });
    let data;
    try { data = await response.json(); }
    catch { throw new Error("The server returned an unreadable response. Please try again."); }
    if (!response.ok) throw new Error(typeof data?.error === "string" ? data.error : "Analysis failed. Please try again.");
    if (!validResult(data)) throw new Error("The server returned an invalid analysis. Please try again.");
    renderResult(data);
  } catch (error) {
    byId("error-message").textContent = error.name === "AbortError"
      ? "The analysis timed out. Please try again."
      : error instanceof TypeError ? "Could not connect to the app. Check that it is running on port 8005 and try again." : error.message;
    showState("error-state");
  } finally {
    clearTimeout(timeout);
    analyzeButton.disabled = false;
    sampleButton.disabled = false;
    message.disabled = false;
    byId("button-label").textContent = "Analyze lead";
    byId("analysis-panel").setAttribute("aria-busy", "false");
  }
});

byId("copy-button").addEventListener("click", async () => {
  if (!currentResult) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(currentResult, null, 2));
    byId("copy-status").textContent = "JSON copied to clipboard.";
  } catch {
    byId("copy-status").textContent = "Clipboard access is unavailable. Open structured JSON and select the text to copy it.";
    document.querySelector(".json-section").open = true;
  }
});
