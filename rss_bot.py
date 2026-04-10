#!/usr/bin/env python3
"""
RSS Discord Bot - Aggregates RSS feeds and posts to Discord
"""

import os
import json
import feedparser
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser


class RSSBot:
    def __init__(self):
        self.feeds = os.environ.get('RSS_FEEDS', '').split(',')
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK', '')
        self.state_file = 'posted_items.json'
        self.posted_items = self.load_state()

    def load_state(self):
        """Load previously posted items from state file"""
        try:
            with open(self.state_file, 'r') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def save_state(self):
        """Save posted items to state file"""
        with open(self.state_file, 'w') as f:
            json.dump(list(self.posted_items), f, indent=2)

    def fetch_feed(self, feed_url):
        """Fetch and parse a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            return feed.entries
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            return []

    def is_recent(self, entry, hours=24):
        """Check if entry is from the last N hours"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            else:
                return True  # If no date, include it

            cutoff = datetime.now() - timedelta(hours=hours)
            return pub_date >= cutoff
        except Exception:
            return True  # If parsing fails, include it

    def get_entry_id(self, entry):
        """Generate unique ID for an entry"""
        if hasattr(entry, 'id'):
            return entry.id
        if hasattr(entry, 'link'):
            return entry.link
        return entry.title

    def format_entry(self, entry, feed_source):
        """Format an RSS entry for Discord"""
        title = entry.get('title', 'No title')
        link = entry.get('link', '')

        # Try to get description/summary
        description = ''
        if hasattr(entry, 'summary'):
            description = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary

        # Detect source type
        source_emoji = self.get_source_emoji(link)

        return {
            'title': title,
            'link': link,
            'description': description,
            'source': feed_source,
            'emoji': source_emoji
        }

    def get_source_emoji(self, link):
        """Get emoji based on source"""
        if 'goodreads.com' in link:
            return '📚'
        elif 'myanimelist.net' in link:
            return '📺'
        else:
            return '🔔'

    def create_discord_message(self, entries):
        """Create formatted Discord message from entries"""
        if not entries:
            return None

        # Group by source
        goodreads_entries = []
        mal_entries = []
        other_entries = []

        for entry in entries:
            if '📚' in entry['emoji']:
                goodreads_entries.append(entry)
            elif '📺' in entry['emoji']:
                mal_entries.append(entry)
            else:
                other_entries.append(entry)

        # Build message
        message_parts = []
        message_parts.append(f"**Daily Update - {datetime.now().strftime('%B %d, %Y')}**\n")

        if goodreads_entries:
            message_parts.append("📚 **Goodreads Updates:**")
            for entry in goodreads_entries:
                message_parts.append(f"• [{entry['title']}]({entry['link']})")
            message_parts.append("")

        if mal_entries:
            message_parts.append("📺 **MyAnimeList Updates:**")
            for entry in mal_entries:
                message_parts.append(f"• [{entry['title']}]({entry['link']})")
            message_parts.append("")

        if other_entries:
            message_parts.append("🔔 **Other Updates:**")
            for entry in other_entries:
                message_parts.append(f"• [{entry['title']}]({entry['link']})")

        return '\n'.join(message_parts)

    def send_to_discord(self, message):
        """Send message to Discord webhook"""
        if not self.discord_webhook:
            print("No Discord webhook configured")
            return False

        data = {
            "content": message
        }

        try:
            response = requests.post(self.discord_webhook, json=data)
            response.raise_for_status()
            print("Message sent to Discord successfully")
            return True
        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return False

    def run(self):
        """Main bot execution"""
        print("Starting RSS Bot...")
        print(f"Monitoring {len(self.feeds)} feeds")

        new_entries = []

        for feed_url in self.feeds:
            feed_url = feed_url.strip()
            if not feed_url:
                continue

            print(f"Fetching: {feed_url}")
            entries = self.fetch_feed(feed_url)

            for entry in entries:
                entry_id = self.get_entry_id(entry)

                # Skip if already posted
                if entry_id in self.posted_items:
                    continue

                # Check if recent (last 24 hours)
                if not self.is_recent(entry, hours=24):
                    continue

                formatted = self.format_entry(entry, feed_url)
                new_entries.append(formatted)
                self.posted_items.add(entry_id)

        print(f"Found {len(new_entries)} new entries")

        if new_entries:
            message = self.create_discord_message(new_entries)
            if message:
                self.send_to_discord(message)
                self.save_state()
                print("Update complete!")
        else:
            print("No new entries to post")


if __name__ == '__main__':
    bot = RSSBot()
    bot.run()
