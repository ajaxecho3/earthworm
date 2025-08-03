# 🌍 Earthworm - Multi-Platform Social Media Data Collection Tool

Earthworm is a powerful, stealth-enabled social media data collection application that supports multiple platforms including Reddit and Twitter. It features a modern web interface built with Vue.js and Flask, providing both command-line and web-based access to social media data collection capabilities.

## ✨ Features

- **Multi-Platform Support**: Currently supports Reddit (with Twitter support planned)
- **Web Dashboard**: Modern, responsive Vue.js interface for easy data collection
- **Stealth Mode**: Advanced anti-bot protection with random delays and rate limiting
- **Real-time Data Collection**: Live progress tracking and background job processing
- **Multiple Export Formats**: Export data as JSON, CSV, or Excel
- **Comment Collection**: Gather both posts and comments with configurable limits
- **Search Functionality**: Search across platforms or specific communities
- **Rate Limiting**: Built-in protection against API rate limits

## 🚀 Quick Start

This project uses the [uv](https://github.com/astral-sh/uv) package manager for fast Python environment management.

### Prerequisites

- Python 3.8+
- uv package manager

### Installation

1. **Install uv** (if not already installed):

   ```bash
   pip install uv
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/ajaxecho3/earthworm.git
   cd earthworm
   ```

3. **Install dependencies**:

   ```bash
   uv sync
   ```

### Running the Application

#### Web Interface (Recommended)

Start the web dashboard for an intuitive interface:

```bash
uv run app/web_ui.py
```

Then open your browser to `http://localhost:5000`

#### Command Line Interface

Run data collection directly from the command line:

```bash
# Navigate to app directory
cd app
uv run main.py

# Or run from root directory
uv run -m app.main
```

## 🔧 Configuration

### Reddit API Setup

1. Create a Reddit application at <https://www.reddit.com/prefs/apps>
2. Create a `.env` file in the project root:

   ```env
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=Earthworm Data Collector 2.0
   ```

### Anti-Bot Configuration

Earthworm includes built-in anti-detection features:

- Random delays between requests (0.3-1.2 seconds)
- Rate limiting (max 30 requests per minute)
- Stealth mode with customizable user agents
- Burst protection

## 📊 Usage Examples

### Web Interface

1. **Initialize Platform**: Select Reddit and enable stealth mode
2. **Search Data**: Enter search terms and configure collection limits
3. **Collect from Subreddits**: Specify subreddit name and sorting method
4. **Export Results**: Download data in your preferred format

### Command Line

```bash
# Search for posts about a topic
uv run -m app.main --search "artificial intelligence" --limit 50

# Collect from specific subreddit
uv run -m app.main --subreddit "MachineLearning" --sort "hot" --limit 25

# Include comments in collection
uv run -m app.main --search "python programming" --comments --limit 20
```

## 🏗️ Project Structure

```text
earthworm/
├── app/
│   ├── main.py              # Core application logic
│   ├── web_ui.py            # Flask web interface
│   ├── adapters/            # Platform-specific adapters
│   │   └── reddit/          # Reddit API integration
│   ├── templates/           # Web UI templates
│   └── utils/               # Utility functions
├── test/                    # Test files
├── pyproject.toml          # Project configuration
├── uv.lock                 # Dependency lock file
└── README.md               # This file
```

## 🔍 Available Platforms

| Platform | Status | Features |
|----------|--------|----------|
| Reddit   | ✅ Active | Posts, comments, subreddit data |
| Twitter  | 🚧 Planned | Tweets, user data, trending topics |

## 📈 Data Collection Capabilities

- **Post Collection**: Title, content, author, score, comments count
- **Comment Collection**: Nested comments with scoring and author info
- **Metadata**: Timestamps, subreddit info, engagement metrics
- **Export Options**: JSON, CSV, Excel formats
- **Real-time Progress**: Live updates during collection

## 🛡️ Ethical Use

Earthworm is designed for research and educational purposes. Please ensure you:

- Respect platform terms of service
- Follow rate limits and API guidelines
- Use collected data responsibly
- Respect user privacy and data protection laws

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:

- New platform integrations
- Feature enhancements
- Bug fixes
- Documentation improvements

## 📝 License

This project is open source. Please check the license file for details.

## 🔗 Links

- **Repository**: <https://github.com/ajaxecho3/earthworm>
- **Issues**: <https://github.com/ajaxecho3/earthworm/issues>
- **uv Package Manager**: <https://github.com/astral-sh/uv>
