#!/bin/bash
# Squad API Status Monitor
# Monitors the status of all Squad API components and services

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local service=$1
    local status=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓${NC} $service"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $service"
    else
        echo -e "${RED}✗${NC} $service"
    fi
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              🖥️  SQUAD API - STATUS MONITOR 🖥️            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Squad API is running
print_info "Checking Squad API status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    API_STATUS="OK"
    API_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null || echo '{"status": "unknown"}')
else
    API_STATUS="FAIL"
fi

print_status "Squad API Server" "$API_STATUS"

# Check if agents endpoint is working
print_info "Testing agents endpoint..."
if curl -s http://localhost:8000/v1/agents > /dev/null 2>&1; then
    AGENTS_STATUS="OK"
else
    AGENTS_STATUS="FAIL"
fi
print_status "Agents Endpoint" "$AGENTS_STATUS"

# Check Docker services
print_info "Checking Docker services..."

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    REDIS_STATUS="OK"
else
    REDIS_STATUS="FAIL"
fi
print_status "Redis" "$REDIS_STATUS"

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U squad -d squad_api > /dev/null 2>&1; then
    POSTGRES_STATUS="OK"
else
    POSTGRES_STATUS="FAIL"
fi
print_status "PostgreSQL" "$POSTGRES_STATUS"

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    PROMETHEUS_STATUS="OK"
else
    PROMETHEUS_STATUS="WARN"
fi
print_status "Prometheus" "$PROMETHEUS_STATUS"

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    GRAFANA_STATUS="OK"
else
    GRAFANA_STATUS="WARN"
fi
print_status "Grafana" "$GRAFANA_STATUS"

# Check running processes
print_info "Checking running processes..."
if pgrep -f "python.*src/main.py" > /dev/null 2>&1; then
    PYTHON_STATUS="OK"
else
    PYTHON_STATUS="FAIL"
fi
print_status "Python Main Process" "$PYTHON_STATUS"

# Check port availability
print_info "Checking port availability..."
if netstat -ln | grep ":8000 " > /dev/null 2>&1; then
    PORT_8000_STATUS="OK"
else
    PORT_8000_STATUS="FAIL"
fi
print_status "Port 8000 (API)" "$PORT_8000_STATUS"

if netstat -ln | grep ":6379 " > /dev/null 2>&1; then
    PORT_6379_STATUS="OK"
else
    PORT_6379_STATUS="FAIL"
fi
print_status "Port 6379 (Redis)" "$PORT_6379_STATUS"

if netstat -ln | grep ":5432 " > /dev/null 2>&1; then
    PORT_5432_STATUS="OK"
else
    PORT_5432_STATUS="FAIL"
fi
print_status "Port 5432 (PostgreSQL)" "$PORT_5432_STATUS"

echo ""
echo "═══════════════════════════════════════════════════════════════"

# Summary
OK_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

for status in "$API_STATUS" "$AGENTS_STATUS" "$REDIS_STATUS" "$POSTGRES_STATUS" "$PROMETHEUS_STATUS" "$GRAFANA_STATUS" "$PYTHON_STATUS" "$PORT_8000_STATUS" "$PORT_6379_STATUS" "$PORT_5432_STATUS"; do
    case $status in
        "OK") ((OK_COUNT++)) ;;
        "WARN") ((WARN_COUNT++)) ;;
        "FAIL") ((FAIL_COUNT++)) ;;
    esac
done

TOTAL_COUNT=$((OK_COUNT + WARN_COUNT + FAIL_COUNT))

echo "📊 SYSTEM STATUS SUMMARY:"
echo "   🟢 Healthy Services: $OK_COUNT"
echo "   🟡 Warning Services: $WARN_COUNT"
echo "   🔴 Failed Services: $FAIL_COUNT"
echo "   📋 Total Services: $TOTAL_COUNT"

# Overall status
if [ $FAIL_COUNT -eq 0 ] && [ $WARN_COUNT -eq 0 ]; then
    OVERALL_STATUS="🟢 EXCELLENT"
    OVERALL_COLOR=$GREEN
elif [ $FAIL_COUNT -eq 0 ]; then
    OVERALL_STATUS="🟡 GOOD"
    OVERALL_COLOR=$YELLOW
else
    OVERALL_STATUS="🔴 NEEDS ATTENTION"
    OVERALL_COLOR=$RED
fi

echo -e "   🎯 Overall Status: ${OVERALL_COLOR}$OVERALL_STATUS${NC}"

echo ""
if [ "$API_STATUS" = "OK" ]; then
    echo -e "💡 ${GREEN}Quick Test Commands:${NC}"
    echo "   • Test API: curl http://localhost:8000/health"
    echo "   • List Agents: curl http://localhost:8000/v1/agents"
    echo "   • Test Agent: python scripts/squad_client.py dev 'Hello World'"
    echo "   • Monitor: python scripts/test_all_agents.py"
elif [ "$API_STATUS" = "FAIL" ]; then
    echo -e "💡 ${RED}Troubleshooting:${NC}"
    echo "   • Start Squad API: activate_squad.bat"
    echo "   • Check logs: docker-compose logs -f"
    echo "   • Restart services: docker-compose restart"
fi

echo ""
if [ "$API_STATUS" = "OK" ]; then
    print_success "Squad API is operational!"
else
    print_error "Squad API needs attention - run activate_squad.bat to start services"
fi

echo ""
