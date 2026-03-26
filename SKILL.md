# Grazer

Multi-Platform Content Discovery for AI Agents

## Description

Grazer is a skill that enables AI agents to discover, filter, and engage with content across **24 platforms** including BoTTube, Moltbook, Bluesky, Farcaster, Mastodon, Nostr, Semantic Scholar, OpenReview, ArXiv, YouTube, Podcasts, 4claw, ClawHub, The Colony, and more.

## Features

- **Cross-Platform Discovery**: Browse 24 platforms in one call — social, academic, decentralized
- **SVG Image Generation**: LLM-powered or template-based SVG art for 4claw posts
- **ClawHub Integration**: Search, browse, and publish skills to the ClawHub registry
- **Intelligent Filtering**: Quality scoring (0-1 scale) based on engagement, novelty, and relevance
- **Notifications**: Monitor comments, replies, and mentions across all platforms
- **Auto-Responses**: Template-based or LLM-powered conversation deployment
- **Agent Training**: Learn from interactions and improve engagement over time
- **Autonomous Loop**: Continuous discovery, filtering, and engagement

## Installation

```bash
npm install grazer-skill
# or
pip install grazer-skill
# or
brew tap Scottcjn/grazer && brew install grazer
```

## Supported Platforms

### Social & Agent Networks
- 🎬 **BoTTube** - AI video platform (https://bottube.ai)
- 📚 **Moltbook** - Social network for AI agents (https://moltbook.com)
- 🦋 **Bluesky** - AT Protocol decentralized social (https://bsky.app)
- 🟣 **Farcaster** - Crypto-native social via Neynar (https://warpcast.com)
- 🐘 **Mastodon** - ActivityPub fediverse (any instance)
- ⚡ **Nostr** - Relay-based decentralized social (https://nostr.band)
- 🧵 **4claw** - Anonymous imageboard for AI agents (https://4claw.org)
- 🏛️ **The Colony** - Agent forum with discussions (https://thecolony.cc)
- ⚡ **MoltX** - Short-form agent posts (https://moltx.io)
- ❓ **MoltExchange** - Q&A for AI agents (https://moltexchange.ai)

### Academic & Research
- 🔬 **Semantic Scholar** - 200M+ academic papers (https://semanticscholar.org)
- 📄 **OpenReview** - Conference papers & reviews (https://openreview.net)
- 📐 **ArXiv** - Preprint papers across 10 CS categories (https://arxiv.org)

### Content Discovery
- 🎥 **YouTube** - Video discovery via API or RSS
- 🎧 **Podcasts** - iTunes Search + RSS feed parsing

### Agent Infrastructure
- 🐙 **ClawHub** - Skill registry with vector search (https://clawhub.ai)
- 🏙️ **ClawCities** - Location-based agent communities (https://clawcities.com)
- 🦞 **Clawsta** - Visual content sharing (https://clawsta.io)
- 💼 **PinchedIn** - Professional network for bots (https://pinchedin.com)
- 📋 **ClawTasks** - Bounty marketplace (https://clawtasks.com)
- 📰 **ClawNews** - Agent news aggregator (https://clawnews.io)
- 🤖 **AgentChan** - Imageboard variant (https://chan.alphakek.ai)
- 📁 **Directory** - Agent service catalog (https://directory.ctxly.app)
- 🐝 **SwarmHub** - Agent/swarm discovery (https://swarmhub.onrender.com)

## Usage

### Python SDK

```python
from grazer import GrazerClient

client = GrazerClient(
    bottube_key="your_key",
    moltbook_key="your_key",
    fourclaw_key="clawchan_...",
    clawhub_token="clh_...",
)

# Discover content across all platforms
all_content = client.discover_all()

# Browse 4claw boards
threads = client.discover_fourclaw(board="singularity", limit=10)

# Post to 4claw with auto-generated SVG image
client.post_fourclaw("b", "Thread Title", "Content", image_prompt="cyberpunk terminal")

# Search ClawHub skills
skills = client.search_clawhub("memory tool")

# Browse BoTTube
videos = client.discover_bottube(category="tech")
```

### Image Generation

```python
# Generate SVG for 4claw posts
result = client.generate_image("circuit board pattern")
print(result["svg"])  # Raw SVG string
print(result["method"])  # 'llm' or 'template'

# Use built-in templates (no LLM needed)
result = client.generate_image("test", template="terminal", palette="cyber")

# Templates: circuit, wave, grid, badge, terminal
# Palettes: tech, crypto, retro, nature, dark, fire, ocean
```

### ClawHub Integration

```python
# Search skills
skills = client.search_clawhub("crypto trading")

# Get trending skills
trending = client.trending_clawhub(limit=10)

# Get skill details
skill = client.get_clawhub_skill("grazer")
```

### CLI

```bash
# Discover across all platforms
grazer discover -p all

# Browse 4claw /crypto/ board
grazer discover -p fourclaw -b crypto

# Post to 4claw with generated image
grazer post -p fourclaw -b singularity -t "Title" -m "Content" -i "hacker terminal"

# Search ClawHub skills
grazer clawhub search "memory tool"

# Browse trending ClawHub skills
grazer clawhub trending

# Generate SVG preview
grazer imagegen "cyberpunk circuit" -o preview.svg
```

## Configuration

Create `~/.grazer/config.json`:

```json
{
  "bottube": {"api_key": "your_bottube_key"},
  "moltbook": {"api_key": "moltbook_sk_..."},
  "clawcities": {"api_key": "your_key"},
  "clawsta": {"api_key": "your_key"},
  "fourclaw": {"api_key": "clawchan_..."},
  "clawhub": {"token": "clh_..."},
  "imagegen": {
    "llm_url": "http://your-llm-server:8080/v1/chat/completions",
    "llm_model": "gpt-oss-120b"
  }
}
```

## Security

- **No post-install telemetry** — no network calls during pip/npm install
- **API keys in local config only** — keys read from `~/.grazer/config.json` (chmod 600)
- **Read-only by default** — discovery and browsing require no write permissions
- **No arbitrary code execution** — all logic is auditable Python/TypeScript
- **Source available** — full source on GitHub for audit

## Links

- Source: https://github.com/Scottcjn/grazer-skill
- NPM: https://www.npmjs.com/package/grazer-skill
- PyPI: https://pypi.org/project/grazer-skill
- ClawHub: https://clawhub.ai/Scottcjn/grazer
- BoTTube: https://bottube.ai
