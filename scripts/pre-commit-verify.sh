#!/bin/bash
#
# Pre-commit verification hook for LearnFlow Triage Service
# Elite Implementation Standard v2.0.0
#
# This script runs before every git commit to ensure code quality
# and compliance with Milestone 2 requirements.
#

set -e  # Exit on any error

echo "=== Pre-Commit Verification ==="
echo "Running elite quality checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}[PASS]${NC} $2"
    else
        echo -e "${RED}[FAIL]${NC} $2"
        exit 1
    fi
}

# 1. Run unit tests
echo -e "\n${YELLOW}1. Running unit tests...${NC}"
python -m pytest backend/triage-service/tests/unit/ -v --tb=short
print_status $? "Unit tests"

# 2. Check for syntax errors
echo -e "\n${YELLOW}2. Checking Python syntax...${NC}"
python -m py_compile backend/triage-service/src/main.py
python -m py_compile backend/triage-service/src/services/integration.py
print_status $? "Python syntax check"

# 3. Validate OpenAI key exists
echo -e "\n${YELLOW}3. Checking OpenAI configuration...${NC}"
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY" .env; then
        echo "OpenAI key found in .env"
    else
        echo -e "${RED}[WARN]${NC} No OPENAI_API_KEY in .env"
    fi
fi

# 4. Check token efficiency
echo -e "\n${YELLOW}4. Running token efficiency check...${NC}"
python scripts/verify-triage-logic.py --phase=0 --silent
print_status $? "Token efficiency (target: 98.7%)"

# 5. Check security middleware
echo -e "\n${YELLOW}5. Validating security middleware...${NC}"
if [ -f "backend/triage-service/src/api/middleware/sanitization.py" ]; then
    echo "Security middleware files present"
else
    echo -e "${RED}[FAIL]${NC} Missing security middleware"
    exit 1
fi

# 6. Check Dapr integration
echo -e "\n${YELLOW}6. Checking Dapr integration...${NC}"
if [ -f "backend/triage-service/src/services/dapr_client.py" ]; then
    echo "Dapr client present"
else
    echo -e "${RED}[WARN]${NC} Dapr client missing"
fi

# 7. Code formatting check (basic)
echo -e "\n${YELLOW}7. Running code style checks...${NC}"
find backend/triage-service/src -name "*.py" -exec python -m py_compile {} \;
print_status $? "All Python files compile"

# 8. Security vulnerability check
echo -e "\n${YELLOW}8. Checking for hardcoded secrets...${NC}"
if grep -r "sk-" backend/triage-service/src/ 2>/dev/null; then
    echo -e "${RED}[FAIL]${NC} Hardcoded API keys found!"
    exit 1
fi
echo "No hardcoded secrets detected"

# 9. Check required files exist
echo -e "\n${YELLOW}9. Verifying required files...${NC}"
required_files=(
    "backend/triage-service/src/main.py"
    "backend/triage-service/src/models/schemas.py"
    "backend/triage-service/src/services/integration.py"
    "backend/triage-service/src/api/middleware/auth.py"
    "backend/triage-service/src/api/middleware/tracing.py"
    "backend/triage-service/src/api/middleware/rate_limiter.py"
    "backend/triage-service/src/api/middleware/sanitization.py"
    "backend/triage-service/src/services/dapr_tracing.py"
    "backend/triage-service/src/services/circuit_breaker_monitor.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}[FAIL]${NC} Missing: $file"
        exit 1
    fi
done
print_status 0 "All required files present"

# 10. Check documentation completeness
echo -e "\n${YELLOW}10. Checking documentation...${NC}"
if [ -f "docs/architecture/98.7-efficiency-proof.md" ]; then
    echo "Architecture documentation present"
else
    echo -e "${YELLOW}[WARN]${NC} Some documentation may be incomplete"
fi

echo -e "\n${GREEN}=== PRE-COMMIT VERIFICATION PASSED ===${NC}"
echo "✅ All checks passed - safe to commit"
echo ""
echo "Ready for Elite Verification:"
echo "  python scripts/verify-triage-logic.py --all-complete"