# m2o - Mastodon to Org-mode Sync Tool

`m2o` is a Python tool that downloads your Mastodon posts (toots) and saves them into an Emacs Org-mode file incrementally. It supports automatic image downloads and attaches them in a format compatible with `org-download` and `org-attach`.

## Features

- **Incremental Sync**: Keeps track of the last synchronized toot ID in `state.json` to fetch only new updates on subsequent runs.
- **Intelligent Org Tree Insertion**: Automatically parses your existing Org-mode file and inserts toots chronologically (ascending order) under the correct Year-Month (`** YYYY-MM MM月`) and Daily (`*** YYYY-MM-DD Weekday`) headings.
- **HTML to Org-mode Formatting**: Cleans up Mastodon HTML content into clean Org-mode plain text, converting mentions, hashtags, and links into standard Org links (`[[URL][Text]]`).
- **Image Attachment Support**:
  - Automatically generates a UUID `:ID:` property inside a `:PROPERTIES:` drawer for toots with images.
  - Downloads images into a structured `.attach/XX/XXXX.../` directory (conforming to `org-attach` guidelines).
  - Inserts `[[attachment:toot_tootID_index.ext]]` links into the Org entry.

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt` (`Mastodon.py`, `beautifulsoup4`, `python-dotenv`, `requests`)

## Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/m-ohtsuka/m2o.git
   cd m2o
   ```

2. **Initialize Python Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   Open `.env` and configure:
   - `MASTODON_INSTANCE_URL`: Your Mastodon instance URL (e.g., `https://mastodon.social`).
   - `MASTODON_ACCESS_TOKEN`: Access token generated from your Mastodon development settings (requires `read:statuses` scope).
   - `ORG_FILE_PATH`: Absolute path to your destination `.org` file (e.g., `/Users/username/org/mastodon.org`).

## Usage

Run the sync script:
```bash
.venv/bin/python m2o.py
```

On the first run, it fetches your latest toots. Subsequent runs will only sync new posts since the last synced ID.

### Automated Synchronization
You can schedule the script to run periodically using `cron`. For example, to sync every hour:
```cron
0 * * * * cd /path/to/m2o && .venv/bin/python m2o.py >/dev/null 2>&1
```

## Testing

You can run automated tests using `pytest`:
```bash
.venv/bin/python -m pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
