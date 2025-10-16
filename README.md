# LLM App Builder

An automated system that builds, deploys, and updates web applications using LLMs and GitHub Pages.

## Features
- Receives build requests via API
- Generates code using Claude/GPT
- Deploys to GitHub Pages automatically
- Handles revision requests

## Setup
1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables in `.env`
4. Run: `uvicorn api.main:app --host 0.0.0.0 --port 8000`

## API Endpoints
- `POST /build` - Build and deploy an app
- `GET /health` - Health check

## License
MIT
