# RSS Discord Bot

A lightweight RSS aggregator bot that monitors multiple RSS feeds and posts daily updates to Discord. Runs automatically via GitHub Actions - no dedicated server required.

## Features

- Monitors multiple RSS feeds (Goodreads, MyAnimeList, and more)
- Aggregates updates into a single daily Discord message
- Tracks posted items to avoid duplicates
- Runs automatically on a schedule via GitHub Actions
- All configuration via GitHub Secrets (keeps feeds private)

## Setup

### 1. Create a Discord Webhook

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Click "New Webhook"
4. Name it (e.g., "RSS Bot")
5. Select the channel where updates should be posted
6. Copy the webhook URL

### 2. Configure GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secrets:

**RSS_FEEDS:**
- Name: `RSS_FEEDS`
- Value: Comma-separated list of RSS feed URLs
- Example: `https://www.goodreads.com/user/updates_rss/YOUR_ID,https://myanimelist.net/rss.php?type=rw&u=YOUR_USERNAME`

**DISCORD_WEBHOOK:**
- Name: `DISCORD_WEBHOOK`
- Value: Your Discord webhook URL from step 1

### 3. Enable GitHub Actions

1. Go to the "Actions" tab in your repository
2. If prompted, click "I understand my workflows, go ahead and enable them"
3. The bot will now run automatically based on the schedule

### 4. Adjust the Schedule (Optional)

Edit `.github/workflows/rss-bot.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: '0 12 * * *'  # Daily at 12:00 PM UTC
```

Common schedules:
- `0 12 * * *` - Daily at noon UTC
- `0 9 * * *` - Daily at 9 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Weekly on Monday

Use [crontab.guru](https://crontab.guru/) to create custom schedules.

### 5. Test the Bot

You can manually trigger the bot to test it:

1. Go to Actions tab
2. Click "RSS Discord Bot" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## How It Works

1. **GitHub Actions** triggers the workflow on schedule
2. **Script runs** and fetches all configured RSS feeds
3. **Filters** for items from the last 24 hours that haven't been posted
4. **Formats** entries by source (Goodreads, MyAnimeList, etc.)
5. **Posts** aggregated message to Discord
6. **Saves state** (posted items) back to the repository

## Project Structure

```
rss-discord-bot/
├── .github/
│   └── workflows/
│       └── rss-bot.yml          # GitHub Actions workflow
├── rss_bot.py                   # Main bot script
├── requirements.txt             # Python dependencies
├── posted_items.json            # State file (auto-generated)
├── .gitignore
└── README.md
```

## Customization

### Adding More Feed Sources

The bot automatically detects Goodreads and MyAnimeList feeds and adds appropriate emojis. To add custom sources:

1. Update the `get_source_emoji()` method in `rss_bot.py`
2. Add your custom domain and emoji

### Changing Message Format

Edit the `create_discord_message()` method in `rss_bot.py` to customize:
- Message structure
- Grouping logic
- Emojis
- Date formatting

### Adjusting Time Window

By default, the bot posts items from the last 24 hours. To change this, modify the `is_recent()` call in the `run()` method:

```python
if not self.is_recent(entry, hours=48):  # Change to 48 hours
    continue
```

## Troubleshooting

### Bot not running

- Check Actions tab for error messages
- Verify GitHub Actions is enabled for your repo
- Check that secrets are set correctly

### No messages posted

- Manually run the workflow to see logs
- Verify RSS feed URLs are correct
- Check if there are actually new items in the feeds

### Duplicate messages

- The `posted_items.json` file tracks what's been posted
- If deleted, the bot may repost old items
- This file is automatically committed by the workflow

## Privacy

- RSS feed URLs are stored in GitHub Secrets (not visible in code)
- Discord webhook is also secret
- Only the aggregated updates are posted publicly

## License

MIT
