const API_BASE = "";

let extractedContent = "";
let currentQuizId = "";
let currentQuestions = [];
let currentQuestionIndex = 0;
let userAnswers = {};

const $ = (id) => document.getElementById(id);

// Initialize
window.addEventListener("DOMContentLoaded", () => {
  initSourceSelection();
  initQuantityButtons();
  initDifficultyButtons();
  initPdfDrop();
  initEventListeners();
  loadSharedQuizIfAny();
});

function initSourceSelection() {
  const urlBtn = $("source-url");
  const pdfBtn = $("source-pdf");
  const urlGroup = $("url-input-group");
  const pdfGroup = $("pdf-input-group");

  urlBtn.addEventListener("click", () => {
    urlBtn.classList.add("active");
    pdfBtn.classList.remove("active");
    urlGroup.classList.remove("hidden");
    pdfGroup.classList.add("hidden");
  });

  pdfBtn.addEventListener("click", () => {
    pdfBtn.classList.add("active");
    urlBtn.classList.remove("active");
    pdfGroup.classList.remove("hidden");
    urlGroup.classList.add("hidden");
  });
}

function initQuantityButtons() {
  document.querySelectorAll(".qty-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".qty-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

function initDifficultyButtons() {
  document.querySelectorAll(".difficulty-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".difficulty-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

function initPdfDrop() {
  const drop = $("pdf-drop");
  const input = $("pdf-file");
  if (!drop || !input) return;

  drop.addEventListener("click", () => input.click());

  input.addEventListener("change", () => {
    const file = input.files?.[0];
    $("pdf-filename").textContent = file ? `✓ ${file.name}` : "";
  });

  ["dragover", "dragenter"].forEach((evt) => {
    drop.addEventListener(evt, (e) => {
      e.preventDefault();
      drop.style.borderColor = "#14b8a6";
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    drop.addEventListener(evt, (e) => {
      e.preventDefault();
      drop.style.borderColor = "#cbd5e1";
    });
  });

  drop.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type === "application/pdf") {
      input.files = e.dataTransfer.files;
      $("pdf-filename").textContent = `✓ ${file.name}`;
    }
  });
}

function initEventListeners() {
  $("extract-pdf").addEventListener("click", extractFromPdf);
  $("extract-url").addEventListener("click", extractFromUrl);
  $("generate-quiz").addEventListener("click", generateQuiz);
  $("prev-question").addEventListener("click", () => navigateQuestion(-1));
  $("next-question").addEventListener("click", () => navigateQuestion(1));
  $("submit-quiz").addEventListener("click", submitQuiz);
  $("results-new-quiz").addEventListener("click", resetAll);
  $("copy-link").addEventListener("click", copyLink);
}

function setStatus(text, kind = "") {
  const el = $("extract-status");
  el.textContent = text || "";
  el.className = `status-text ${kind}`;
}

function setGenerateStatus(text, kind = "") {
  const el = $("generate-status");
  el.textContent = text || "";
  el.className = `status-text ${kind}`;
}

async function extractFromPdf() {
  const input = $("pdf-file");
  const file = input.files?.[0];
  if (!file) {
    setStatus("Please choose a PDF first.", "error");
    return;
  }
  setStatus("Extracting text from PDF…", "info");
  try {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/upload/pdf`, {
      method: "POST",
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Extraction failed.");
    extractedContent = data.content;
    setStatus("Text extracted successfully!", "success");
  } catch (err) {
    setStatus(String(err), "error");
  }
}

async function extractFromUrl() {
  const url = $("url-input").value.trim();
  if (!url) {
    setStatus("Please enter a URL.", "error");
    return;
  }
  setStatus("Extracting text from URL…", "info");
  try {
    const res = await fetch(`${API_BASE}/upload/url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Extraction failed.");
    extractedContent = data.content;
    setStatus("Text extracted successfully!", "success");
  } catch (err) {
    setStatus(String(err), "error");
  }
}

async function generateQuiz() {
  if (!extractedContent) {
    setGenerateStatus("Please extract content first.", "error");
    return;
  }

  const difficultyBtn = document.querySelector(".difficulty-btn.active");
  const qtyBtn = document.querySelector(".qty-btn.active");
  const difficulty = difficultyBtn?.getAttribute("data-difficulty") || "medium";
  const numQuestions = parseInt(qtyBtn?.getAttribute("data-qty") || "10");

  setGenerateStatus("Generating quiz with local LLM… this may take a minute.", "info");
  $("generate-quiz").disabled = true;

  try {
    const res = await fetch(`${API_BASE}/generate-quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: extractedContent,
        source_type: "text",
        source_label: null,
        difficulty,
        num_questions: numQuestions,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Quiz generation failed.");

    currentQuizId = data.quiz_id;
    currentQuestions = data.questions;
    currentQuestionIndex = 0;
    userAnswers = {};
    
    showQuiz();
    updateShareLink();
    setGenerateStatus("Quiz generated!", "success");
  } catch (err) {
    setGenerateStatus(`${String(err)}. Ensure Ollama is running.`, "error");
  } finally {
    $("generate-quiz").disabled = false;
  }
}

function showQuiz() {
  $("step-settings").classList.add("hidden");
  $("step-quiz").classList.remove("hidden");
  renderQuestion();
}

function renderQuestion() {
  if (currentQuestionIndex >= currentQuestions.length) return;

  const question = currentQuestions[currentQuestionIndex];
  const totalQuestions = currentQuestions.length;
  const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
  const answeredCount = Object.keys(userAnswers).length;

  // Update header
  $("question-counter").textContent = `Question ${currentQuestionIndex + 1} of ${totalQuestions}`;
  $("progress-fill").style.width = `${progress}%`;
  $("answered-count").textContent = answeredCount;

  // Update question text
  $("question-text").textContent = question.question;

  // Render options
  const container = $("options-container");
  container.innerHTML = "";
  const letters = ["A", "B", "C", "D"];
  
  question.options.forEach((opt, idx) => {
    const letter = letters[idx];
    const isSelected = userAnswers[currentQuestionIndex] === letter;
    
    const optionDiv = document.createElement("div");
    optionDiv.className = `option-item ${isSelected ? "selected" : ""}`;
    
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = `question-${currentQuestionIndex}`;
    radio.value = letter;
    radio.checked = isSelected;
    radio.addEventListener("change", () => selectAnswer(letter));
    
    const label = document.createElement("label");
    label.textContent = `${letter}. ${opt}`;
    label.addEventListener("click", () => {
      radio.checked = true;
      selectAnswer(letter);
    });
    
    optionDiv.appendChild(radio);
    optionDiv.appendChild(label);
    container.appendChild(optionDiv);
  });

  // Update navigation buttons
  $("prev-question").disabled = currentQuestionIndex === 0;
  
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;
  $("next-question").classList.toggle("hidden", isLastQuestion);
  $("submit-quiz").classList.toggle("hidden", !isLastQuestion);
}

function selectAnswer(letter) {
  userAnswers[currentQuestionIndex] = letter;
  renderQuestion(); // Re-render to update selected state and answered count
}

function navigateQuestion(direction) {
  const newIndex = currentQuestionIndex + direction;
  if (newIndex >= 0 && newIndex < currentQuestions.length) {
    currentQuestionIndex = newIndex;
    renderQuestion();
  }
}

async function submitQuiz() {
  if (!currentQuizId) return;
  
  const answeredCount = Object.keys(userAnswers).length;
  if (answeredCount === 0) {
    alert("Please answer at least one question.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/submit-quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quiz_id: currentQuizId, answers: userAnswers }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Submit failed.");

    showResults(data);
  } catch (err) {
    alert(String(err));
  }
}

function showResults(data) {
  $("step-quiz").classList.add("hidden");
  $("step-results").classList.remove("hidden");

  const percentage = Math.round(data.percentage);
  $("score-percentage").textContent = `${percentage}%`;
  $("score-line").textContent = `Score: ${data.score} / ${data.total}`;
  
  let message = "";
  if (percentage >= 90) message = "🎉 Excellent work!";
  else if (percentage >= 70) message = "👍 Great job!";
  else if (percentage >= 50) message = "📚 Good effort!";
  else message = "💪 Keep practicing!";
  
  $("score-message").textContent = message;
  updateShareLink();
}

function updateShareLink() {
  if (!currentQuizId) return;
  const url = new URL(window.location.href);
  url.searchParams.set("quiz_id", currentQuizId);
  $("share-link").value = url.toString();
}

function copyLink() {
  const input = $("share-link");
  if (!input.value) return;
  input.select();
  document.execCommand("copy");
  const btn = $("copy-link");
  const originalText = btn.textContent;
  btn.textContent = "Copied!";
  setTimeout(() => {
    btn.textContent = originalText;
  }, 2000);
}

async function loadSharedQuizIfAny() {
  const url = new URL(window.location.href);
  const quizId = url.searchParams.get("quiz_id");
  if (!quizId) return;

  try {
    const res = await fetch(`${API_BASE}/quiz/${quizId}`);
    const data = await res.json();
    if (!res.ok) return;
    
    currentQuizId = data.quiz_id;
    currentQuestions = data.questions.map((q) => ({
      question: q.question,
      options: q.options,
    }));
    currentQuestionIndex = 0;
    userAnswers = {};
    
    showQuiz();
    updateShareLink();
  } catch {
    // ignore; normal create-new flow
  }
}

function resetAll() {
  extractedContent = "";
  currentQuizId = "";
  currentQuestions = [];
  currentQuestionIndex = 0;
  userAnswers = {};
  
  $("step-settings").classList.remove("hidden");
  $("step-quiz").classList.add("hidden");
  $("step-results").classList.add("hidden");
  
  $("pdf-filename").textContent = "";
  $("pdf-file").value = "";
  $("url-input").value = "";
  setStatus("");
  setGenerateStatus("");
  
  // Reset buttons
  document.querySelectorAll(".qty-btn").forEach((b) => b.classList.remove("active"));
  document.querySelector(".qty-btn[data-qty='10']").classList.add("active");
  
  document.querySelectorAll(".difficulty-btn").forEach((b) => b.classList.remove("active"));
  document.querySelector(".difficulty-btn[data-difficulty='medium']").classList.add("active");
}
