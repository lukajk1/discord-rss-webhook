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
        # Support both comma-separated and newline-separated feeds
        feeds_raw = os.environ.get('RSS_FEEDS', '')
        if '\n' in feeds_raw:
            self.feeds = [f.strip() for f in feeds_raw.split('\n') if f.strip()]
        else:
            self.feeds = [f.strip() for f in feeds_raw.split(',') if f.strip()]

        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK', '')
        self.state_file = 'posted_items.json'
        self.posted_items = self.load_state()

        # Get number of days to look back (default: 1)
        self.days_back = int(os.environ.get('DAYS_BACK', '1'))

        # Get whether to ignore history (default: false)
        self.ignore_history = os.environ.get('IGNORE_HISTORY', 'false').lower() == 'true'

    def load_state(self):
        """Load previously posted items from state file"""
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                # Handle both old format (list of strings) and new format (dict with timestamps)
                if isinstance(data, list):
                    # Convert old format to new format with current timestamp
                    return {item: datetime.now().isoformat() for item in data}
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_state(self):
        """Save posted items to state file"""
        # Clean up old entries (older than 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        cleaned_items = {
            item_id: timestamp
            for item_id, timestamp in self.posted_items.items()
            if datetime.fromisoformat(timestamp) >= cutoff_date
        }

        items_removed = len(self.posted_items) - len(cleaned_items)
        if items_removed > 0:
            print(f"Cleaned up {items_removed} old items (>30 days)")

        with open(self.state_file, 'w') as f:
            json.dump(cleaned_items, f, indent=2)

    def fetch_feed(self, feed_url):
        """Fetch and parse a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            return feed
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            return None

    def extract_username(self, feed):
        """Extract username from feed metadata"""
        if not feed or not hasattr(feed, 'feed'):
            return None

        feed_title = feed.feed.get('title', '')

        # Goodreads: "Miranda's Updates"
        if "'s Updates" in feed_title or "'s updates" in feed_title:
            return feed_title.replace("'s Updates", "").replace("'s updates", "").strip()

        # MyAnimeList: "Chocd's Anime from MyAnimeList.net"
        if "'s Anime from MyAnimeList" in feed_title or "'s Manga from MyAnimeList" in feed_title:
            return feed_title.split("'s")[0].strip()

        return None

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

    def extract_image_url(self, html_content):
        """Extract image URL from HTML content (for Goodreads)"""
        if not html_content:
            return None

        # Look for img src in the HTML
        import re
        match = re.search(r'<img[^>]+src="([^"]+)"', html_content)
        if match:
            img_url = match.group(1)
            # Upgrade to larger image if it's a thumbnail
            img_url = img_url.replace('_SX50_', '_SX200_').replace('_SY75_', '_SY200_')
            return img_url
        return None

    def format_entry(self, entry, feed_source, username=None):
        """Format an RSS entry for Discord"""
        title = entry.get('title', 'No title')
        link = entry.get('link', '')

        # Try to get description/summary and extract image
        description = ''
        image_url = None
        if hasattr(entry, 'summary'):
            description = entry.summary
            image_url = self.extract_image_url(description)

        # Detect source type
        source_emoji = self.get_source_emoji(link)

        return {
            'title': title,
            'link': link,
            'description': description,
            'source': feed_source,
            'emoji': source_emoji,
            'username': username,
            'image_url': image_url
        }

    def get_source_emoji(self, link):
        """Get emoji based on source"""
        if 'goodreads.com' in link:
            return '📚'
        elif 'myanimelist.net' in link:
            return '📺'
        else:
            return '🔔'

    def create_discord_messages(self, entries):
        """Create formatted Discord messages from entries (separated by user and platform)"""
        if not entries:
            return []

        # Group by platform and user
        from collections import defaultdict
        goodreads_by_user = defaultdict(list)
        mal_by_user = defaultdict(list)
        other_by_user = defaultdict(list)

        for entry in entries:
            username = entry.get('username', 'Unknown')
            if '📚' in entry['emoji']:
                goodreads_by_user[username].append(entry)
            elif '📺' in entry['emoji']:
                mal_by_user[username].append(entry)
            else:
                other_by_user[username].append(entry)

        messages = []
        date_str = datetime.now().strftime('%B %d, %Y')

        # Create separate message for each user's Goodreads updates
        for username, user_entries in sorted(goodreads_by_user.items()):
            message_parts = []
            message_parts.append(f"It's the Pony Express! Here's the latest Goodreads updates for {date_str}:\n")
            message_parts.append(f"**{username}'s Updates:**")

            for entry in user_entries:
                # Strip username from title but keep the verb
                title = entry['title']
                if entry.get('username') and title.startswith(entry['username']):
                    import re
                    title = re.sub(f"^{re.escape(entry['username'])} ", "", title)

                # Include image if available
                if entry.get('image_url'):
                    message_parts.append(f"• [{title}]({entry['link']}) [Cover]({entry['image_url']})")
                else:
                    message_parts.append(f"• [{title}]({entry['link']})")

            messages.append('\n'.join(message_parts))

        # Create separate message for each user's MAL updates
        for username, user_entries in sorted(mal_by_user.items()):
            message_parts = []
            message_parts.append(f"It's the Pony Express! Here's the latest MyAnimeList updates for {date_str}:\n")
            message_parts.append(f"**{username}'s Updates:**")

            for entry in user_entries:
                message_parts.append(f"• [{entry['title']}]({entry['link']})")

            messages.append('\n'.join(message_parts))

        # Create message for other updates (grouped by user)
        for username, user_entries in sorted(other_by_user.items()):
            message_parts = []
            message_parts.append(f"It's the Pony Express! Here's the latest updates for {date_str}:\n")
            message_parts.append(f"**{username}'s Updates:**")

            for entry in user_entries:
                message_parts.append(f"• [{entry['title']}]({entry['link']})")

            messages.append('\n'.join(message_parts))

        return messages

    def send_to_discord(self, message):
        """Send message to Discord webhook"""
        if not self.discord_webhook:
            print("No Discord webhook configured")
            return False

        # Discord has a 2000 character limit
        if len(message) > 2000:
            print(f"Message too long ({len(message)} chars), truncating...")
            message = message[:1997] + "..."

        data = {
            "content": message,
            "flags": 4096  # SUPPRESS_NOTIFICATIONS flag
        }

        try:
            response = requests.post(self.discord_webhook, json=data)
            response.raise_for_status()
            print("Message sent to Discord successfully")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"Error sending to Discord: {e}")
            print(f"Response: {response.text}")
            print(f"Message length: {len(message)} characters")
            return False
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
            feed = self.fetch_feed(feed_url)

            if not feed or not hasattr(feed, 'entries'):
                continue

            # Extract username from feed metadata
            username = self.extract_username(feed)

            for entry in feed.entries:
                entry_id = self.get_entry_id(entry)

                # Skip if already posted (unless ignoring history)
                if not self.ignore_history and entry_id in self.posted_items:
                    continue

                # Check if recent (based on days_back setting)
                hours = self.days_back * 24
                if not self.is_recent(entry, hours=hours):
                    continue

                formatted = self.format_entry(entry, feed_url, username)
                new_entries.append(formatted)
                self.posted_items[entry_id] = datetime.now().isoformat()

        print(f"Found {len(new_entries)} new entries")

        if new_entries:
            messages = self.create_discord_messages(new_entries)
            if messages:
                for i, message in enumerate(messages, 1):
                    print(f"Sending message {i}/{len(messages)}...")
                    self.send_to_discord(message)
                self.save_state()
                print("Update complete!")
        else:
            print("No new entries to post")


if __name__ == '__main__':
    bot = RSSBot()
    bot.run()
