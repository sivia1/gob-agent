#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  GOB - Government Job Agent | Setup Script
#  Run this once to get everything started.
#  Usage: bash setup.sh
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on any error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   GOB - Government Job Agent  🤖     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Check Docker ─────────────────────────────────────────
echo -e "${YELLOW}[1/4] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop from https://docker.com${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# ── Step 2: Create .env file ─────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/4] Setting up environment file...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env already exists — skipping (edit it manually if needed)${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env from template${NC}"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: You need to fill in your API keys in .env before continuing!${NC}"
    echo -e "   Open .env in your editor and fill in:"
    echo -e "   - FIRECRAWL_API_KEY  → https://firecrawl.dev"
    echo -e "   - GEMINI_API_KEY     → https://aistudio.google.com"
    echo -e "   - TELEGRAM_BOT_TOKEN → via @BotFather on Telegram"
    echo -e "   - TELEGRAM_CHAT_ID   → your chat/group ID"
    echo ""
    echo -e "   Once filled, run ${BLUE}bash setup.sh${NC} again."
    exit 0
fi

# ── Step 3: Check .env is filled ─────────────────────────────────
echo ""
echo -e "${YELLOW}[3/4] Checking your API keys...${NC}"

source .env

KEYS_OK=true

if [[ "$FIRECRAWL_API_KEY" == "fc-your-key-here" || -z "$FIRECRAWL_API_KEY" ]]; then
    echo -e "${RED}❌ FIRECRAWL_API_KEY not set in .env${NC}"
    KEYS_OK=false
fi

if [[ "$GEMINI_API_KEY" == "AIza-your-key-here" || -z "$GEMINI_API_KEY" ]]; then
    echo -e "${RED}❌ GEMINI_API_KEY not set in .env${NC}"
    KEYS_OK=false
fi

if [[ "$TELEGRAM_BOT_TOKEN" == "123456:ABC-your-token-here" || -z "$TELEGRAM_BOT_TOKEN" ]]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not set in .env${NC}"
    KEYS_OK=false
fi

if [[ "$TELEGRAM_CHAT_ID" == "your-chat-id-here" || -z "$TELEGRAM_CHAT_ID" ]]; then
    echo -e "${RED}❌ TELEGRAM_CHAT_ID not set in .env${NC}"
    KEYS_OK=false
fi

if [ "$KEYS_OK" = false ]; then
    echo ""
    echo -e "${YELLOW}Please fill in all values in .env and run setup.sh again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API keys look filled in${NC}"

# ── Step 4: Start Docker services ────────────────────────────────
echo ""
echo -e "${YELLOW}[4/4] Starting GOB services (n8n + backend)...${NC}"
echo -e "   This might take a minute on first run (downloading images)."
echo ""

docker compose up -d --build

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   GOB is running! Here's where to go:               ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║   n8n UI:        http://localhost:5678               ║${NC}"
echo -e "${GREEN}║   Backend API:   http://localhost:8000               ║${NC}"
echo -e "${GREEN}║   API Docs:      http://localhost:8000/docs          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next step: Open http://localhost:5678 and import the workflow${NC}"
echo -e "${BLUE}           File: n8n-workflow/gob-workflow.json${NC}"
echo ""
echo -e "To stop GOB:    ${YELLOW}docker compose down${NC}"
echo -e "To view logs:   ${YELLOW}docker compose logs -f${NC}"
echo ""
