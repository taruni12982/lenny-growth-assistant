const form = document.querySelector("#chat-form");
const questionInput = document.querySelector("#question");
const chat = document.querySelector("#chat");
const sendButton = document.querySelector("#send-button");
const statusMessage = document.querySelector("#status-message");
const suggestionButtons = document.querySelectorAll(".suggestion");

function addMessage(className, text) {
  const message = document.createElement("article");
  message.className = `message ${className}`;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  message.appendChild(paragraph);
  chat.appendChild(message);
  message.scrollIntoView({ behavior: "smooth", block: "end" });
  return message;
}

function addSources(sources) {
  const wrapper = document.createElement("section");
  wrapper.className = "sources";
  const label = document.createElement("p");
  label.className = "sources-label";
  label.textContent = "Sources used";
  wrapper.appendChild(label);
  sources.forEach((source) => {
    const card = document.createElement("article");
    card.className = "source";
    const heading = document.createElement("h3");
    heading.textContent = `Source ${source.number}: ${source.title}`;
    const speaker = document.createElement("small");
    speaker.textContent = `Speaker: ${source.speaker}`;
    const excerpt = document.createElement("p");
    excerpt.textContent = source.excerpt;
    const terms = document.createElement("small");
    terms.textContent = `Matched keywords: ${source.matched_terms.join(", ")}`;
    card.append(heading, speaker, excerpt, terms);
    wrapper.appendChild(card);
  });
  chat.appendChild(wrapper);
  wrapper.scrollIntoView({ behavior: "smooth", block: "end" });
}

function addLoadingMessage() {
  const message = document.createElement("article");
  message.className = "message assistant loading";
  message.setAttribute("aria-label", "Searching sources and preparing an answer");
  message.textContent = "Searching demo sources and preparing your answer...";
  chat.appendChild(message);
  message.scrollIntoView({ behavior: "smooth", block: "end" });
  return message;
}

async function getResponsePayload(response) {
  try { return await response.json(); } catch { return {}; }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  addMessage("user", question);
  questionInput.value = "";
  sendButton.disabled = true;
  sendButton.querySelector("span").textContent = "Thinking...";
  statusMessage.textContent = "Searching the fictional demo transcripts...";
  const loadingMessage = addLoadingMessage();
  try {
    const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
    const payload = await getResponsePayload(response);
    if (!response.ok) throw new Error(payload.detail || "The server could not complete that request. Please try again.");
    addMessage("assistant", payload.answer);
    addSources(payload.sources);
    statusMessage.textContent = "Answer ready. Sources are shown below it.";
  } catch (error) {
    addMessage("error", error.message || "Unable to contact the server. Check that the app and Ollama are running, then try again.");
    statusMessage.textContent = "The request could not be completed.";
  } finally {
    loadingMessage.remove();
    sendButton.disabled = false;
    sendButton.querySelector("span").textContent = "Ask";
    questionInput.focus();
  }
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => { questionInput.value = button.textContent; questionInput.focus(); });
});
