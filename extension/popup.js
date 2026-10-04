const backendUrl = "http://127.0.0.1:8000/summarize";

const sourceText = document.getElementById("sourceText");
const summaryEl = document.getElementById("summary");
const metricsEl = document.getElementById("metrics");
const statusEl = document.getElementById("status");
const summarizeButton = document.getElementById("summarize");
const pasteSelectionButton = document.getElementById("pasteSelection");

const setStatus = (message, error = false) => {
  statusEl.textContent = message;
  statusEl.style.color = error ? "#d93025" : "#111";
};

const fetchSelection = async () => {
  setStatus("Loading selected text...");

  try {
    const stored = await chrome.storage.local.get("selectedText");
    const text = stored.selectedText || "";

    if (!text) {
      setStatus("Select some text in the page first.", true);
      return;
    }

    sourceText.value = text;
    setStatus("Selected text loaded. Ready to summarize.");
  } catch (error) {
    console.error(error);
    setStatus("Failed to fetch selected text.", true);
  }
};

const summarizeText = async () => {
  const text = sourceText.value.trim();
  if (!text) {
    setStatus("Enter or select text to summarize.", true);
    return;
  }

  summaryEl.textContent = "";
  metricsEl.textContent = "";
  setStatus("Summarizing...");

  try {
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, max_length: 120, min_length: 25 }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      setStatus(errorData.error || "Summarization backend error.", true);
      return;
    }

    const data = await response.json();
    summaryEl.textContent = data.summary || "No summary returned.";
    const originalWords = data.original_word_count ?? 0;
    const summaryWords = data.summary_word_count ?? 0;
    const reduction = data.reduction_percentage ?? 0;
    metricsEl.innerHTML = `Original: ${originalWords} words<br>Summary: ${summaryWords} words<br>Reduction: ${reduction}%`;
    setStatus("Summary complete.");
  } catch (error) {
    console.error(error);
    setStatus("Unable to reach backend. Start the FastAPI server.", true);
  }
};

pasteSelectionButton.addEventListener("click", fetchSelection);
summarizeButton.addEventListener("click", summarizeText);
