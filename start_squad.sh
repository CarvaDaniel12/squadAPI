#!/bin/bash
#
# Squad API - One-Command Startup Script
# Starts entire stack: Redis, PostgreSQL, Prometheus, Grafana, API
#
# Usage: ./start_squad.sh
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           🚀 SQUAD API - FULL STACK STARTUP 🚀            ║"
echo "║                                                            ║"
echo "║  Transform External LLMs into BMad Specialists            ║"
echo "║  Orchestrated by You - Local AI Controller                ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} ${YELLOW}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Check Python
print_step "Step 1/6: Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Step 2: Activate virtual environment
print_step "Step 2/6: Activating virtual environment..."
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Creating..."
    python3 -m venv venv
fi
source venv/bin/activate
print_success "Virtual environment activated"

# Step 3: Load environment variables
print_step "Step 3/6: Loading environment variables..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env created from .env.example"
    else
        print_error ".env file not found and .env.example not available"
        exit 1
    fi
fi
export $(cat .env | xargs)
print_success "Environment variables loaded from .env"

# Step 4: Check Docker and start services
print_step "Step 4/6: Starting Docker Compose services..."
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker Desktop or Docker Engine"
    exit 1
fi

docker-compose up -d
print_success "Docker Compose services started"

# Step 5: Wait for services
print_step "Step 5/6: Waiting for services to be healthy..."
sleep 5

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is healthy"
else
    print_error "Redis failed to start"
    docker-compose logs redis
    exit 1
fi

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U squad -d squad_api > /dev/null 2>&1; then
    print_success "PostgreSQL is healthy"
else
    print_error "PostgreSQL failed to start"
    docker-compose logs postgres
    exit 1
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus is healthy"
else
    print_error "Prometheus failed to start"
fi

# Step 6: Start API
print_step "Step 6/6: Starting Squad API..."
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║             ✅ ALL SERVICES STARTED SUCCESSFULLY ✅        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Squad API Stack Ready!${NC}"
echo ""
echo "📍 Service Endpoints:"
echo "  🌐 API:        ${BLUE}http://localhost:8000${NC}"
echo "  📚 Swagger:    ${BLUE}http://localhost:8000/docs${NC}"
echo "  📊 Prometheus: ${BLUE}http://localhost:9090${NC}"
echo "  📉 Grafana:    ${BLUE}http://localhost:3000${NC} (admin/admin)"
echo "  💾 Redis:      ${BLUE}localhost:6379${NC}"
echo "  🗄️  PostgreSQL: ${BLUE}localhost:5432${NC}"
echo ""
echo "📋 Useful Commands:"
echo "  🔍 Check API:      curl http://localhost:8000/health"
echo "  📊 List Agents:    curl http://localhost:8000/agents"
echo "  📈 Check Providers: curl http://localhost:8000/providers"
echo "  🛑 Stop Services:  docker-compose down"
echo "  📋 View Logs:      docker-compose logs -f squad-api"
echo ""
echo "🚀 Starting API server on port 8000..."
echo ""

# Start the API
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
