# YouTube Management Interview Tracker

Daily, free, cloud-hosted tracker for genuine management interviews (CEO/MD/CFO
interviews, earnings calls, analyst/investor meets) on your watchlist companies.
Runs on GitHub Actions — no server, no laptop needed, no paid subscription.

## Setup (one-time, ~10 min)

### 1. Get a YouTube Data API key (free)
- Go to https://console.cloud.google.com/
- Create a project → Enable "YouTube Data API v3"
- Create credentials → API key
- Free quota: 10,000 units/day (each search ≈ 100 units → ~100 searches/day free,
  comfortably covers hundreds of companies at 1 search/day each)

### 2. Create a Telegram bot (free)
- Message **@BotFather** on Telegram → `/newbot` → follow prompts → copy the **bot token**
- Message your new bot once (anything), then visit:
  `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
  and copy your **chat_id** from the response

### 3. Push this repo to GitHub
Create a new (can be private) GitHub repo and push these files to it.

### 4. Add secrets
In the repo: **Settings → Secrets and variables → Actions → New repository secret**
- `YOUTUBE_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 5. Done
The workflow runs daily at 8:30 AM IST automatically. You can also trigger it
manually anytime from the **Actions** tab → "Daily YouTube Management Interview
Check" → **Run workflow**.

## Expanding the watchlist
Just add rows to `watchlist.csv` — no code changes needed:
```
company,search_query
TANFAC,TANFAC Industries
Sona BLW,Sona Comstar
NewCompany,New Company Ltd
```
Scales to hundreds of companies within the free API quota.

## How filtering works
- **Includes**: interview, MD/CEO/CFO interview, concall, earnings call, analyst
  meet, investor conference, etc.
- **Excludes**: target price, buy/sell calls, technical analysis, chart patterns,
  trading strategy content — even if they mention the company name.
- Fully rule-based (no AI/API cost) — tune the keyword lists in `tracker.py` anytime.

## Future enhancement (optional)
Add an AI-generated summary of each interview's key takeaways by piping the
video's transcript (via `youtube-transcript-api`, also free) through an LLM
before sending the Telegram alert. Not included now to keep the system 100% free
and dependency-light — happy to add this later if useful.
