# YouTube Autopilot for PastMysteryFiles

**Automated YouTube channel management system with 95% automation and human oversight**

## Overview

This system provides comprehensive automation for the PastMysteryFiles YouTube channel, handling everything from content processing to analytics, while maintaining human control over critical decisions through a Go/No-Go approval system.

### Channel Information
- **Channel**: PastMysteryFiles (@pastmysteryfiles-l5g)
- **Theme**: Uncovering History's Greatest Mysteries
- **Host**: Professor Archibald Blackwood
- **Target Audience**: History enthusiasts, mystery lovers, educational content seekers

## Features

### 🤖 Automated Content Pipeline
- **Video Processing**: Automatic transcription using Whisper
- **SEO Generation**: AI-powered titles, descriptions, and tags
- **Thumbnail Creation**: SDXL-generated professional thumbnails
- **Shorts Creation**: HeyGen avatar videos for daily engagement
- **Upload & Scheduling**: Automated YouTube publishing

### 📊 Analytics & Monitoring
- **Daily KPI Tracking**: CTR, APV, engagement metrics
- **Performance Guardrails**: Automatic alerts for underperforming content
- **Weekly Reports**: Comprehensive performance analysis
- **Trend Analysis**: Topic mining and content recommendations

### 🧪 A/B Testing
- **Title Testing**: Multiple variants with performance tracking
- **Thumbnail Testing**: Visual optimization
- **Avatar Testing**: Different HeyGen avatars for Shorts

### 🎛️ Management Dashboard
- **Content Queue**: Review and approve pending uploads
- **Performance Overview**: Real-time channel metrics
- **Experiment Management**: A/B test control and results
- **Moderation Tools**: Comment review and management

## Project Structure

```
youtube-autopilot/
├── .github/workflows/          # GitHub Actions workflows
├── configs/                    # Configuration files
├── dash/                      # Streamlit dashboard
├── data/                      # Analytics and reports
│   ├── analytics/
│   ├── reports/
│   └── cache/
├── experiments/               # A/B testing data
├── scripts/                   # Core automation scripts
├── videos_inbox/             # Input video files
├── thumbnails_out/           # Generated thumbnails
└── subtitles_out/            # Generated subtitles
```

## Technology Stack

- **Language Models**: Qwen-2.5-7B-Instruct, Mistral-7B-Instruct
- **Image Generation**: Stable Diffusion XL 1.0
- **Video Generation**: HeyGen API (avatar videos)
- **Speech Recognition**: Faster-Whisper Large-v3
- **Content Moderation**: Detoxify/Toxic-BERT
- **Dashboard**: Streamlit
- **Orchestration**: GitHub Actions
- **Data Storage**: DuckDB, JSON files

## Quick Start

### Prerequisites
1. GitHub repository with Actions enabled
2. YouTube Data API credentials
3. HeyGen API access
4. Stable Diffusion XL endpoint (local or cloud)

### Setup
1. Configure GitHub Secrets (see `docs/setup.md`)
2. Install dependencies: `pip install -r scripts/requirements.txt`
3. Configure `configs/config.yaml`
4. Run initial setup: `python scripts/setup.py`

### Usage
1. **Add Content**: Place video/audio files in `videos_inbox/`
2. **Review**: Check dashboard for generated SEO and thumbnails
3. **Approve**: Use Go/No-Go buttons in dashboard
4. **Monitor**: Track performance in analytics dashboard

## Workflows

### Content Pipeline (Twice Weekly)
- Triggers: Tuesday & Friday 09:00 UTC
- Process: Transcribe → Generate SEO → Create Thumbnails → Upload (pending approval)

### Daily Shorts (HeyGen)
- Triggers: Daily 15:00 UTC
- Process: Extract key points → Generate avatar video → Schedule (pending approval)

### Analytics Collection (Daily)
- Triggers: Daily 06:00 UTC
- Process: Fetch YouTube metrics → Generate reports → Check guardrails

### Weekly Brief (Mondays)
- Triggers: Monday 07:00 UTC
- Process: Analyze trends → Mine topics → Plan A/B tests → Generate recommendations

## Human Oversight

The system requires human approval for:
- ✅ Final content publishing
- ✅ Schedule changes
- ✅ Thumbnail/title changes
- ✅ Comment moderation actions
- ✅ A/B test implementations

Automated actions include:
- 🤖 Content processing and SEO generation
- 🤖 Analytics collection and reporting
- 🤖 Performance monitoring and alerts
- 🤖 Draft creation for all content types

## License & Compliance

This project uses only commercially licensed models and tools:
- ✅ Mistral, Qwen, Llama (commercial use approved)
- ✅ Stable Diffusion XL (OpenRAIL++)
- ✅ Whisper (MIT)
- ✅ Detoxify (MIT)
- ❌ Flux.1-dev (not used - license restrictions)

## Support

For setup assistance or troubleshooting, see the documentation in the `docs/` folder or open an issue.

---

**Built with ❤️ for PastMysteryFiles - Uncovering History's Greatest Mysteries**
