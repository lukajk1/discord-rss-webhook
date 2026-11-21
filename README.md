# RSS Discord Bot

A lightweight RSS aggregator bot that monitors multiple RSS feeds and posts daily updates to Discord. Runs automatically via GitHub Actions - no dedicated server required.

## What It Does

- Monitors RSS feeds (Goodreads, MyAnimeList, and more)
- Aggregates updates into a single daily Discord message (sent silently)
- Tracks posted items to avoid duplicates
- Runs automatically on a schedule via GitHub Actions
- Feeds kept in a local, gitignored `feeds.txt` and synced to a GitHub Secret (keeps feeds private)

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
├── feeds.txt                  # Your feed URLs (gitignored)
├── feeds.example.txt          # Template for feeds.txt
├── sync-feeds.ps1             # Push feeds.txt to the RSS_FEEDS secret
├── requirements.txt           # Python dependencies
├── posted_items.json          # State file (auto-generated)
└── README.md
```

## Configuration

**Feeds:** the list lives in `feeds.txt`, one URL per line, `#` for comments.
It is gitignored (the repo is public); copy `feeds.example.txt` to start one.
The bot reads `feeds.txt` when it exists, otherwise the `RSS_FEEDS` env var.

GitHub Actions can't see the local file, so after editing it push it to the
`RSS_FEEDS` secret (needs the GitHub CLI, signed in):

```powershell
.\sync-feeds.ps1
```

**GitHub Secrets:**
- `RSS_FEEDS` - the feed URLs, newline-separated (set by `sync-feeds.ps1`)
- `DISCORD_WEBHOOK` - Discord webhook URL

**Schedule:** Modify cron schedule in `.github/workflows/rss-discord-bot.yml`

## License

MIT
