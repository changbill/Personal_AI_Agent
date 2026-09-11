const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const messages = document.querySelector("#messages");
const sessionId = crypto.randomUUID();
const userId = "personal-user";

function addMessage(text, kind) {
  const message = document.createElement("p");
  message.className = `message ${kind}`;
  message.textContent = text;
  messages.append(message);
  message.scrollIntoView({ block: "end" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";
  const button = form.querySelector("button");
  button.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, session_id: sessionId, message: text }),
    });
    if (!response.ok) throw new Error("응답을 생성하지 못했습니다.");
    const data = await response.json();
    addMessage(data.response, "assistant");
  } catch (error) {
    addMessage(error.message, "error");
  } finally {
    button.disabled = false;
    input.focus();
  }
});
