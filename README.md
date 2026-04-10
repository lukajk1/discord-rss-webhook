# RSS Discord Bot

A lightweight RSS aggregator bot that monitors multiple RSS feeds and posts daily updates to Discord. Runs automatically via GitHub Actions - no dedicated server required.

## What It Does

- Monitors RSS feeds (Goodreads, MyAnimeList, and more)
- Aggregates updates into a single daily Discord message (sent silently)
- Tracks posted items to avoid duplicates
- Runs automatically on a schedule via GitHub Actions
- All configuration via GitHub Secrets (keeps feeds private)

## How It Works

1. GitHub Actions triggers the workflow on schedule (daily at 12:00 PM UTC)
2. Script fetches all configured RSS feeds
3. Filters for items from the last 24 hours that haven't been posted
4. Formats entries by source (📚 Goodreads, 📺 MyAnimeList, etc.)
5. Posts aggregated message to Discord silently
6. Saves state (posted items) back to the repository

## Project Structure

```
rss-discord-bot/
├── .github/workflows/
│   ├── rss-discord-bot.yml    # Main RSS bot workflow
│   └── test.yml               # Test Discord message workflow
├── rss_bot.py                 # Main bot script
├── requirements.txt           # Python dependencies
├── posted_items.json          # State file (auto-generated)
└── README.md
```

## Configuration

**GitHub Secrets:**
- `RSS_FEEDS` - Newline or comma-separated list of RSS feed URLs
- `DISCORD_WEBHOOK` - Discord webhook URL

**Schedule:** Modify cron schedule in `.github/workflows/rss-discord-bot.yml`

## License

MIT
