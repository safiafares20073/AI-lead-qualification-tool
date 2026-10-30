# Verified behavior

Validation was performed in this checkout on 2026-10-30.

- Installed the pinned Python dependencies in `.venv` and repeated installation from `requirements.txt` successfully.
- Started the actual Flask server on **port 8005** with debug mode off.
- `node --check static/app.js`: passed.
- `python -m unittest discover -s tests -v`: **6 tests passed**, covering input rejection, missing-key behavior, response contract, boundary scores, mismatched priorities, malformed and truncated provider output, and sanitized upstream failures. Provider success/error fixtures are used only in unit tests, never by the application.
- Real Chromium browser checks against the running server: GET `/` returned the customer-facing HTML page; every JavaScript element ID exists; no page JavaScript errors occurred.
- The sample button filled the textbox with the specified inquiry and produced **zero additional network requests**.
- Analyze sent a real, same-origin `POST /qualify` with the textbox message. The loading indicator appeared and controls were disabled while the request was in flight. Controls recovered after completion.
- The actual server returned **HTTP 503**, and the page displayed its exact clear error: `Cohere is not configured. Add COHERE_API_KEY to the project's local .env file, then restart the app.`
- Desktop and 375px mobile screenshots were inspected/generated. Mobile had no horizontal overflow.
- `.env` and `.venv` are ignored by Git. No `.env` was present, created, overwritten, or committed; no key values were printed.

## Remaining live check

No successful Cohere analysis or successful-result clipboard action has been verified live, because this checkout has no `.env` key. Add a valid `COHERE_API_KEY` to the local `.env`, restart the app, and analyze the sample. The output must come from Cohere; the app has no fallback analysis. The host also needs outbound HTTPS access to `api.cohere.com`.

The Windows PowerShell commands in README are provided for reproduction; they were not executed in this Linux environment. Functional tests were run using the equivalent Linux commands.
