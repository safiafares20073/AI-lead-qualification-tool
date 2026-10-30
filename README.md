# Leadlight — Lead Qualification & CRM Automation prototype

A small Python/Flask customer demo using Cohere directly. Paste an ordinary lead inquiry, analyze it, review the details and suggested reply, and copy structured JSON for a future CRM step. No database or CRM integration is included. No analysis is stored by the app. Inquiries are sent to Cohere; its account and retention policies apply.

## Run on Windows (PowerShell)

From this project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://localhost:8005/**. Local runs use port **8005** by default. When deployed, the app uses the hosting provider's `PORT`. This is a demo, not a production-ready CRM service.

The app reads `COHERE_API_KEY` from `.env` beside `app.py` using python-dotenv. Preserve any existing `.env`; if the key is missing, add it locally using your editor, then restart the server. Never commit or share that file. `.gitignore` excludes it. Existing process variables take precedence. The key stays on the server. The model is `command-a-03-2025` through `https://api.cohere.com/v2/chat`; network access to `api.cohere.com` and account/model access are required. TLS verification stays enabled.

For Linux/macOS, use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python app.py`.

## Deploy on Render

The included `render.yaml` configures a free Render web service. To deploy:

1. Create a new GitHub repository and upload the **contents of this project folder** to its root. Do not upload `.env`, `.venv`, or API keys. Keep `render.yaml` at the repository root.
2. In Render, choose **New > Blueprint**, connect that GitHub repository, and create the service.
3. When prompted, enter your Cohere key for `COHERE_API_KEY` in Render's secret environment-variable field. Never add the key to GitHub.
4. Wait for the deployment to finish, open the generated `onrender.com` URL, and test a lead.

Render's free web services can spin down after 15 minutes without traffic, so the first visit after inactivity may take longer. The app still sends each inquiry to Cohere; the Cohere account and retention policies apply.

## Use the demo

1. Paste an inquiry, or choose **Use sample message**. The sample button only fills the textbox; it does not submit or make an API request.
2. Choose **Analyze lead** to send `POST /qualify` on the same origin. The page shows a loading state and then either validated Cohere output or a clear error.
3. Review all extracted details, score, priority, summary, and suggested reply. **View structured JSON** and **Copy JSON** provide a CRM-ready object; nothing is sent to a CRM.

Success returns exactly: `name`, `company`, `email`, `phone`, `need`, `budget`, `timeline`, `category`, `intent`, `score`, `priority`, `summary`, `suggested_reply`. Only absent extracted details may be null. The score must be an integer from 0 to 100; priority must be low (0–39), medium (40–69), or high (70–100). Invalid provider output is rejected, never repaired with fabricated analysis. Missing configuration, provider failure, and invalid input return non-2xx JSON containing an `error` message.

The prompt requests grounded extraction and a reply without invented commitments. Model output still needs human review; structural validation cannot prove factual correctness.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check static/app.js
```

Node is optional and only used for JavaScript syntax checking. Unit tests use isolated provider fixtures to check request shape, response validation, and failure handling; they do not prove live model access. The application has no mock mode or fallback results.

## Current validation

The initial checkout was empty and had no `.env`. The demo was built in this checkout. See `VALIDATION.md` for actual browser and API results. A successful live analysis requires your own valid Cohere key; no live success is claimed without it.
