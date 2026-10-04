# Smart Email Summarizer

A simple tool that summarizes long emails or articles using a local NLP backend and a Chrome extension popup.

## What is included

- `backend/app.py`: FastAPI service running a Hugging Face summarization model.
- `backend/requirements.txt`: Python dependencies for the backend.
- `extension/manifest.json`: Chrome extension manifest.
- `extension/popup.html`: Extension popup UI.
- `extension/popup.js`: Popup logic to send text to the backend.
- `extension/style.css`: Popup styling.

## Setup

1. Install Python dependencies:

```bash 
pip install -r requirements.txt
```

2. Start the backend server:

```bash
uvicorn app:app --reload
```

3. Load the extension in Chrome:

- Open `chrome://extensions`
- Enable "Developer mode"
- Click "Load unpacked"
- Select the `extension` folder

4. Use it:

- Open an email or article page in Chrome
- Select text and click "Use selected text"
- Click "Summarize"

## Notes

- The backend currently uses `sshleifer/distilbart-cnn-12-6` for summarization.
- The extension communicates with `http://127.0.0.1:8000` by default.
- For a production version, deploy the backend and update `backendUrl` in `extension/popup.js`.
