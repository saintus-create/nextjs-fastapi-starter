#!/usr/bin/env bash
#
# cline-agent installer
# Usage: curl -sSL https://get.cline-agent.com | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "   _____ _ _                                        _   "
echo "  / ____| (_)                                      | |  "
echo " | |    | |_ _ __   ___    __ _  __ _  ___ _ __ | |_ "
echo " | |    | | | '_ \ / _ \  / _\` |/ _\` |/ _ \ '_ \| __|"
echo " | |____| | | | | |  __/ | (_| | (_| |  __/ | | | |_ "
echo "  \_____|_|_|_| |_|\___|  \__,_|\__, |\___|_| |_|\__|"
echo "                                  __/ |               "
echo "                                 |___/                "
echo -e "${NC}"
echo -e "${GREEN}Terminal-first autonomous coding agent${NC}"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Please install Python 3.10+ and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${YELLOW}→ Detected Python $PYTHON_VERSION${NC}"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip is required but not installed.${NC}"
    exit 1
fi

# Install cline-agent
echo -e "${YELLOW}→ Installing cline-agent...${NC}"
pip3 install --upgrade cline-agent

# Create config directory
CONFIG_DIR="$HOME/.cline-agent"
if [ ! -d "$CONFIG_DIR" ]; then
    echo -e "${YELLOW}→ Creating config directory at $CONFIG_DIR${NC}"
    mkdir -p "$CONFIG_DIR"
fi

# Create sample .env if it doesn't exist
ENV_FILE="$CONFIG_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}→ Creating sample .env file${NC}"
    cat > "$ENV_FILE" << 'EOF'
# cline-agent configuration
# Add your API keys below

# OpenAI (recommended)
OPENAI_API_KEY=sk-your-key-here

# Optional: Additional providers
# GROQ_API_KEY=gsk-your-key-here
# SAMBA_API_KEY=sk-your-key-here
EOF
    echo -e "${YELLOW}   Edit $ENV_FILE to add your API keys${NC}"
fi

# Verify installation
echo ""
if command -v cline-agent &> /dev/null; then
    echo -e "${GREEN}✓ cline-agent installed successfully!${NC}"
    echo ""
    echo -e "Next steps:"
    echo -e "  1. Add your API key to ${BLUE}~/.cline-agent/.env${NC}"
    echo -e "  2. Run ${BLUE}cline-agent --help${NC} to see available commands"
    echo -e "  3. Try ${BLUE}cline-agent task \"Create a hello.py file\"${NC}"
    echo ""
    echo -e "${GREEN}Happy coding! 🚀${NC}"
else
    echo -e "${RED}Installation may have succeeded but cline-agent is not in PATH.${NC}"
    echo "Try running: python3 -m cline_agent --help"
fi
