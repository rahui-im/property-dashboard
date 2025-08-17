# 🏢 Samsung-dong Property Dashboard

강남구 삼성1동 부동산 매물 통합 대시보드

## 📊 Overview

This project collects and visualizes real estate properties in Samsung-dong, Gangnam-gu, Seoul from multiple platforms:

- **Naver Real Estate** (네이버 부동산)
- **Zigbang** (직방)
- **Dabang** (다방)
- **KB Real Estate** (KB부동산)

## 🚀 Features

- **Multi-platform Integration**: Collects data from 4 major real estate platforms
- **Real-time Dashboard**: Interactive web dashboard built with Next.js
- **Data Analytics**: Price analysis, property type distribution, and market insights
- **Responsive Design**: Works on desktop and mobile devices

## 📈 Statistics

- **Total Properties**: 3,340+
- **Platforms**: 4
- **Property Types**: Apartments, Officetels, Villas, Studios
- **Trade Types**: Sale, Lease, Monthly Rent

## 🛠️ Tech Stack

- **Frontend**: Next.js, React, Recharts
- **Backend**: Python, AsyncIO
- **Data Collection**: BeautifulSoup, aiohttp, Playwright
- **Deployment**: Vercel

## 🔗 Live Demo

Visit: [Your Vercel URL will be here]

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/[your-username]/property-collector.git

# Install dependencies
npm install

# Run development server
npm run dev
```

## 🏗️ Project Structure

```
property-collector/
├── pages/           # Next.js pages
├── components/      # React components
├── public/          # Static assets
├── src/             # Python crawlers
│   ├── mcp/        # MCP orchestrator
│   └── agents/     # Collection agents
└── data/           # Collected data
```

## 📊 Data Sources

1. **Naver Real Estate**: 840 properties
2. **Zigbang**: 500 properties
3. **Dabang**: 1,200 properties
4. **KB Real Estate**: 800 properties

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 👨‍💻 Author

Created with ❤️ by [Your Name]

---

**Note**: This project is for educational purposes. Please respect the terms of service of each platform when collecting data.