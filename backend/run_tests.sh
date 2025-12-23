#!/bin/bash

# Test runner script for VAS Backend
# Usage: ./run_tests.sh [phase]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}VAS Backend Test Suite${NC}"
echo "========================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

# Get phase from command line argument
PHASE=${1:-"all"}

case $PHASE in
    phase1|p1|1)
        echo -e "${GREEN}Running Phase 1 tests...${NC}"
        pytest tests/test_phase1_foundation.py -v -m phase1
        echo -e "${GREEN}Phase 1 tests complete!${NC}"
        ;;
    phase2|p2|2)
        echo -e "${GREEN}Running Phase 2 tests...${NC}"
        pytest tests/test_phase2_apis.py -v -m phase2
        echo -e "${GREEN}Phase 2 tests complete!${NC}"
        ;;
    incremental|inc)
        echo -e "${GREEN}Running incremental tests...${NC}"
        pytest tests/test_incremental.py -v
        echo -e "${GREEN}Incremental tests complete!${NC}"
        ;;
    all|*)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest tests/ -v
        echo -e "${GREEN}All tests complete!${NC}"
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Test Summary:${NC}"
echo -e "${BLUE}========================================${NC}"


