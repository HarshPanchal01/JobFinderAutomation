# Job Finder Automation

A Python-based automation tool that scrapes job listings from Google Jobs via SerpApi, filters them (salary/date/keywords/etc.), and generates a report. You can either run it manually on your computer **when you want**, or let GitHub run it **on a schedule** and email you automatically.

## Choose how you want to run it

There are two options:

| Setup                          | What it is                  | Runs where       | Runs when                               | Best for                                    |
| ------------------------------ | --------------------------- | ---------------- | --------------------------------------- | ------------------------------------------- |
| **Manual (Local)**             | You run the script yourself | Your laptop/PC   | Only when you run a command             | Testing, tweaking filters, one-off runs     |
| **Scheduled (GitHub Actions)** | GitHub runs it for you      | GitHub’s servers | Automatically on a weekly cron schedule | Automated runs, no input is needed from you |

## Table of Contents

- [Features](#features)
- [Setup A: Scheduled weekly run (GitHub Actions)](#setup-a-scheduled-weekly-run-github-actions)
- [Setup B: Manual run on your computer (Local)](#setup-b-manual-run-on-your-computer-local)
- [Configuration reference (environment variables and secrets)](#configuration-reference-environment-variables-and-secrets)
- [Search Logic & API](#search-logic--api)
- [Adding New Queries/Locations](#adding-new-querieslocations)
- [License](#license)

## Features

- **Automated Search**: Fetches jobs for multiple queries and locations.
- **Smart Filtering**:
  - **Salary**: Filters out jobs below a minimum salary.
  - **Date**: Ignores jobs older than $X$ days.
  - **Keywords**: Excludes jobs with specific keywords in the title.
  - **Companies**: Blacklists specific companies.
  - **Sources**: Filters for reputable sources (e.g., LinkedIn, Indeed).
- **Deduplication**: Tracks job history to ensure you never see the same job twice.
- **Reporting**: Generates a Markdown summary and a JSON data file.
- **Email Notifications**: Sends a full "Weekly Jobs Report" directly to your inbox.
- **GitHub Actions Automation**: Can run weekly on a schedule and archive results in the form of GitHub Issues.
- **Dockerized**: Consistent environment locally and in CI.

---

## Setup A: Scheduled weekly run (GitHub Actions)

### What you get

- Weekly (scheduled) run on GitHub’s servers
- Email report to your inbox
- Deduplication across weeks via a `job-history-data` branch

### Step-by-step setup

1. **Fork this repo** (so you can store your own secrets/variables).
2. In your fork, go to **Actions** and click **Enable workflows** (GitHub often disables them by default on new forks).
3. Go to **Settings → Secrets and variables → Actions**.
4. Add **Repository Secrets**:
   - `API_KEY` (your [SerpApi](https://serpapi.com/) key)
   - `EMAIL_PASSWORD` (your email provider [app-password](https://support.google.com/mail/answer/185833))
5. Add **Repository Variables** (these are not encrypted, so don’t put passwords here):
   - `EMAIL_ADDRESS` (sender email)
   - `EMAIL_RECEIVER` (JSON list or comma-separated string)
   - Optional config like `SEARCH_QUERIES`, `LOCATIONS`, `MIN_SALARY`, etc. (see [Configuration reference](#configuration-reference-environment-variables-and-secrets))

### Running it now (without waiting a week)

1. Go to **Actions → Job Finder Automation**.
2. Click **Run workflow**.
3. (Optional) provide inputs like `search_queries` or `locations` to override the saved variables for that one run.

### Changing the schedule

The schedule is defined in `.github/workflows/job_finder.yml` under `on.schedule.cron`.

- Current cron: `47 4 * * 4` (GitHub cron is interpreted in **UTC**)
- Use a cron helper like https://crontab.guru/ and convert to your local timezone.

---

## Setup B: Manual run on your computer (Local)

This option is for running the job search **manually**.

### Option 1: Docker (recommended)

Docker is easiest because it matches the GitHub Actions environment.

1. **Install Docker** (Docker Desktop on Windows/Mac, or Docker Engine on Linux).
2. **Create a `.env` file** in the repo root (see example below).
3. **Build the image**:
   ```bash
   docker build -t job-finder .
   ```
4. **Run it** (saves `jobs.md` + `jobs.json` to your folder):

   ```bash
   # Windows (Command Prompt)
   docker run --rm -v "%cd%:/app" --env-file .env job-finder

   # Windows (PowerShell)
   docker run --rm -v "${PWD}:/app" --env-file .env job-finder

   # Linux/WSL/Mac
   docker run --rm -v "$(pwd):/app" --env-file .env job-finder
   ```

### Option 2: Python directly

1. **Install Python**: 3.11+
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Create a `.env` file** in the repo root.
4. **Run**:
   ```bash
   python src/main.py
   ```

### Example `.env`

```env
API_KEY=your_serpapi_key
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# JSON list OR comma-separated is supported for lists
EMAIL_RECEIVER=["you@gmail.com", "other@gmail.com"]

SEARCH_QUERIES=["python developer", "backend engineer"]
LOCATIONS=["Toronto, Ontario, Canada", "Montreal, Quebec, Canada"]

GOOGLE_DOMAIN=google.ca
GL=ca
HL=en

TRUSTED_DOMAINS=["linkedin", "indeed"]
MAX_PAGES=5
MIN_SALARY=50000
MAX_DAYS_OLD=7
SCHEDULE_TYPES=["full-time", "part-time"]
BLACKLIST_COMPANIES=["hooli", "pied piper"]
EXCLUDE_KEYWORDS=["manager", "co-op"]
```

---

## Configuration reference (environment variables and secrets)

The application is configured using environment variables.

Where you set them depends on how you run it:

- **Local**: put them in a `.env` file
- **GitHub Actions**: put them in **Secrets** and **Variables** (as described above)

| Variable                        | Description                                                                                                   | Default                                                              |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------- |
| `API_KEY` (**Required**)        | Your [SerpApi](https://serpapi.com/) API Key.                                                                 | `None`                                                               |
| `SEARCH_QUERIES`                | List of job titles to search for.                                                                             | `["software developer"]`                                             |
| `LOCATIONS`                     | List of locations to search in.                                                                               | `["Toronto, Ontario, Canada"]`                                       |
| `MAX_PAGES`                     | Max pages to fetch per query/location.                                                                        | `5`                                                                  |
| `MIN_SALARY`                    | Minimum annual salary.                                                                                        | `50000`                                                              |
| `MAX_DAYS_OLD`                  | Max age of job posting in days.                                                                               | `7`                                                                  |
| `BLACKLIST_COMPANIES`           | Companies to exclude.                                                                                         | `[]`                                                                 |
| `EXCLUDE_KEYWORDS`              | Keywords to exclude from titles.                                                                              | `[]`                                                                 |
| `SCHEDULE_TYPES`                | Allowed schedule types (e.g., Full-time).                                                                     | `["Full-time"]`                                                      |
| `TRUSTED_DOMAINS`               | Allowed application sources. If set but empty (e.g. `[]`), filtering is disabled and all domains are allowed. | `["linkedin", "glassdoor", "indeed", "ziprecruiter", "simplyhired"]` |
| `GOOGLE_DOMAIN`                 | Google domain to use.                                                                                         | `google.ca`                                                          |
| `GL`                            | Country code.                                                                                                 | `ca`                                                                 |
| `HL`                            | Language code.                                                                                                | `en`                                                                 |
| `EMAIL_ADDRESS` (**Required**)  | Sender email address for notifications.                                                                       | `None`                                                               |
| `EMAIL_PASSWORD` (**Required**) | Email [app-password](https://support.google.com/mail/answer/185833).                                          | `None`                                                               |
| `EMAIL_RECEIVER`                | List of recipient emails (JSON list or comma-separated).                                                      | Defaults to `EMAIL_ADDRESS`                                          |
| `SMTP_SERVER`                   | SMTP server for sending emails.                                                                               | `smtp.gmail.com`                                                     |
| `SMTP_PORT`                     | SMTP port (usually 587 for TLS or 465 for SSL).                                                               | `587`                                                                |

---

## Search Logic & API

### SerpApi

This project uses the [SerpApi Google Jobs API](https://serpapi.com/google-jobs-api).

- **Engine**: `google_jobs`
- **Limits**: Be aware of your SerpApi plan limits. Each page of results counts as 1 search.
  - _Formula_: `(Queries * Locations * Max_Pages) = Total API Calls`

### Deduplication & Filtering

1.  **Intra-run**: Removes duplicates found within the same search session.
2.  **Inter-run**: Checks `data/history.json` to ensure you don't see the same job ID from last week.
3.  **Quality Filters**:
    - **Regex Matching**: Ensures keywords like "lead" don't accidentally filter "Leading Company".
    - **Source Validation**: Prioritizes direct company sites or trusted boards (LinkedIn, Indeed) over spammy aggregators.

---

## Adding New Queries/Locations

You don't need to change code! Just update your `.env` file or GitHub Repository Variables.

**Note relating to Locations**: Please use the full location name (e.g. "Toronto, Ontario, Canada" instead of "Toronto, ON"). The system automatically handles formatting for US and Canadian locations to optimize search results. For international locations, the full string provided will be used.

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.
