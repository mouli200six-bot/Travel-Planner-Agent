# India Travel Planner AI

A fully static, single-file AI travel planning assistant for India, powered by **IBM watsonx Granite-4**.  
Works locally (open `index.html` directly), via Flask, or deployed on **GitHub Pages** — no server needed.

---

## IMPORTANT — API Key Setup (Read First)

> **Your original API key was disabled by IBM Cloud** because it was detected in a public GitHub repository.  
> IBM Cloud automatically scans GitHub and revokes any exposed keys for security reasons.  
> You **must generate a new API key** before using this app.

### Step 1 — Generate a new IBM Cloud API key

1. Log in to [IBM Cloud Console](https://cloud.ibm.com)
2. Click your account name (top-right) → **Manage** → **Access (IAM)**
3. In the left sidebar click **API keys**
4. Click **Create an IBM Cloud API key**
5. Name it (e.g. `travel-planner-key`) and click **Create**
6. **Copy the key immediately** — it is only shown once

### Step 2 — Add the key to index.html

Open `index.html` and find this line near the top of the `<script>` block:

```js
const IBM_API_KEY = "YOUR_IBM_API_KEY_HERE";
```

Replace `YOUR_IBM_API_KEY_HERE` with your new key.

### Step 3 — Never commit API keys to public repos

Add a `.gitignore` entry or use GitHub Secrets / environment variables for production.  
If you accidentally push a key, IBM will disable it within minutes.

---

## Running Locally

### Option A — Open directly (no server)

Just double-click `index.html` — it calls IBM watsonx directly from the browser.

### Option B — Via Flask (optional backend)

```bash
pip install -r requirements.txt
python app.py
```
Open **http://localhost:5000**

---

## Deploying on GitHub Pages

1. Push the repo to GitHub (make sure `index.html` is in the root or `docs/` folder)
2. Go to **Settings → Pages** in your repository
3. Set **Source** to `Deploy from a branch`, branch `main`, folder `/ (root)`
4. Click **Save** — your site will be live at `https://<your-username>.github.io/<repo-name>/`

> **Important:** GitHub Pages serves only static files. The Flask `app.py` does NOT run on GitHub Pages — only `index.html` is used there, which calls IBM watsonx directly from the browser. This is the correct setup.

---

## Project Structure

```
.
├── index.html       ← Entire app (self-contained, works on GitHub Pages)
├── app.py           ← Optional Flask backend (for local use with Python)
├── requirements.txt ← Python dependencies (Flask only)
└── README.md
```

---

## Configuration (inside index.html)

| Variable       | Description                              | Where to change        |
|----------------|------------------------------------------|------------------------|
| `IBM_API_KEY`  | IBM Cloud API key                        | Line ~378 in index.html|
| `IBM_PROJECT`  | watsonx project ID (PromptLab)           | Line ~379 in index.html|
| `IBM_MODEL`    | Model ID                                 | Line ~380 in index.html|

---

## Tech Stack

- **Frontend**: Pure HTML5 / CSS3 / Vanilla JS — zero dependencies, no build step
- **AI Model**: IBM watsonx · Granite-4-h-small (`ibm/granite-4-h-small`)
- **Auth**: IBM IAM token fetched directly in the browser (refreshed automatically)
- **Backend (optional)**: Python Flask (only needed for local `python app.py` mode)
