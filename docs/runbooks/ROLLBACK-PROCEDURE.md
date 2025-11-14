# Rollback Procedure - Story 9.8
# Squad API Emergency Rollback Guide
# Date: 2025-11-13 | Epic 9: Production Readiness

## 🚨 WHEN TO ROLLBACK

### Immediate Rollback Triggers (P1)
- [ ] Error rate > 1% sustained for 5 minutes
- [ ] P95 latency > 10 seconds sustained
- [ ] Database connectivity lost
- [ ] All providers failing
- [ ] Memory/CPU consumption critical
- [ ] Data corruption detected
- [ ] Security vulnerability discovered in production

### Escalation Rollback Triggers (P2)
- [ ] Error rate > 0.5% for 10 minutes
- [ ] Agent routing broken
- [ ] >5% 429 rate limit errors
- [ ] Audit logging not working
- [ ] PII redaction bypass detected

### Decision Window: 2-5 minutes max
- Assess severity immediately
- Make rollback decision quickly
- Better to rollback and investigate than risk customer impact

---

## 🔄 ROLLBACK DECISION MATRIX

| Issue | Error Rate | Latency | Decision | Speed |
|-------|-----------|---------|----------|-------|
| Data corruption | Any | Any | ROLLBACK | Immediate |
| All providers down | >1% | N/A | ROLLBACK | Immediate |
| Database lost | Any | N/A | ROLLBACK | Immediate |
| Security breach | Any | Any | ROLLBACK | Immediate |
| High error spike | >1% | >5s | ROLLBACK | <2 min |
| Degraded latency | <0.5% | >3s | INVESTIGATE | 5 min |
| Rate limiting issues | <0.5% | Normal | MONITOR | 10 min |

---

## ⏱️ ROLLBACK TIMELINE

```
T+0:00   Problem detected
T+0:30   Incident declared → War room assembled
T+1:00   Assessment complete → Rollback decision made
T+1:30   Rollback execution started
T+3:00   Rollback complete → Traffic resumed
T+5:00   Full validation complete
T+10:00  Post-incident review started
```

---

## 🔧 TECHNICAL ROLLBACK STEPS

### Phase 1: Immediate Stabilization (T+0 to T+30 sec)

#### Step 1.1: Declare Incident
```bash
# Slack notification
@channel 🚨 INCIDENT: Production deployment issue detected
Severity: P1 | Issue: [Brief description]
Incident Commander: [Name]
Status: Investigating
```

#### Step 1.2: Pause Traffic (Load Balancer)
```bash
# Option A: AWS ELB / ALB
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --target-type ip \
  --health-check-enabled=false

# Option B: Nginx
# Set upstream to maintenance page
server {
    listen 80;
    location / {
        return 503;
    }
}
systemctl reload nginx

# Option C: Kubernetes
kubectl patch svc squad-api -p '{"spec":{"selector":{"app":"squad-api-v1"}}}'
```

#### Step 1.3: Alert On-Call Team
```bash
# Trigger PagerDuty / On-call system
pd trigger \
  --incident-key production-rollback \
  --description "Production rollback initiated" \
  --urgency high

# Slack DM to on-call engineers
```

### Phase 2: Prepare Rollback (T+30 sec to T+1 min)

#### Step 2.1: Verify Rollback Target
```bash
# Get previous stable version
git describe --tags --abbrev=0
# Output: v1.0.0-beta

# Verify image exists
docker inspect squad-api:v1.0.0-beta
# Verify: Image ID, tag, date

# Check database backup
aws rds describe-db-snapshots \
  --db-snapshot-identifier squad-api-pre-deploy
# Status: available
```

#### Step 2.2: Notify Stakeholders
```bash
# Message: In #incident-response channel
📋 Rollback Plan:
- Current version: v1.0.1 (deployed 2 min ago)
- Rollback target: v1.0.0 (stable, known good)
- Database: Restore from pre-deploy snapshot
- Expected downtime: 2-3 minutes
- Estimated completion: T+3 min

Deployment Lead: [Name]
On-Call: [Name]
Status: Standing by for approval...

React with ✅ to proceed with rollback
```

### Phase 3: Execute Rollback (T+1 to T+3 min)

#### Option A: Kubernetes Rollback
```bash
# Get rollout history
kubectl rollout history deployment squad-api

# Show details of previous revision
kubectl rollout history deployment squad-api --revision=2

# Rollback to previous stable version
kubectl rollout undo deployment squad-api
# Deployment rolled back to revision 2

# Watch rollout progress
kubectl rollout status deployment squad-api --timeout=5m

# Verify all pods are running
kubectl get pods -l app=squad-api
NAME                      READY   STATUS    RESTARTS
squad-api-v1-abc123       1/1     Running   0
squad-api-v1-def456       1/1     Running   0
squad-api-v1-ghi789       1/1     Running   0
```

#### Option B: Docker Compose Rollback
```bash
# Stop current containers
docker-compose down

# Switch to previous version
sed -i 's/squad-api:v1.0.1/squad-api:v1.0.0/g' docker-compose.yml

# Start previous version
docker-compose up -d

# Verify running
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option C: Manual Server Rollback
```bash
# SSH to production server
ssh prod-server.example.com

# Stop current services
systemctl stop squad-api
systemctl stop nginx

# Checkout previous version
cd /app/squad-api
git fetch origin
git checkout v1.0.0
git log --oneline -1
# Verify: v1.0.0 commit hash

# Install dependencies (if changed)
pip install -r requirements.txt

# Start previous version
systemctl start squad-api
systemctl start nginx

# Verify running
systemctl status squad-api
```

#### Step 3.1: Database Rollback (If Needed)
```bash
# Check if migrations need to be reversed
python manage.py showmigrations
# Previous version migrations: X
# Current version migrations: Y

# If schema changed: restore from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier squad-api-rollback \
  --db-snapshot-identifier squad-api-pre-deploy \
  --no-multi-az

# Point application to restored database
export DATABASE_URL="postgresql://user:pass@squad-api-rollback:5432/squad_api"
systemctl restart squad-api
```

#### Step 3.2: Cache Invalidation (If Needed)
```bash
# Flush Redis cache to ensure consistency
redis-cli FLUSHALL
# Response: OK

# Restart cache connections in app
systemctl restart squad-api

# Alternative: Selective flush
redis-cli FLUSHDB ASYNC
```

### Phase 4: Verify Rollback Success (T+3 to T+5 min)

#### Step 4.1: Health Checks
```bash
# Direct health endpoint test
curl -i https://api.squad-api.example.com/health
# Expected: HTTP/1.1 200 OK

# Verify all required endpoints
for endpoint in /health /providers /v1/agents/code /metrics; do
  echo "Testing: $endpoint"
  curl -s https://api.squad-api.example.com$endpoint | head -c 100
  echo ""
done
```

#### Step 4.2: Error Rate Verification
```bash
# Check Prometheus metrics
# Query: rate(http_requests_total{status=~"5.."}[5m])
# Expected: < 0.001 (less than 0.1%)

# Check logs for errors
kubectl logs deployment/squad-api --since=1m | grep ERROR | wc -l
# Expected: 0

# Check application metrics
curl -s https://api.squad-api.example.com/metrics | grep http_requests_total
# Expected: baseline values, not spiking
```

#### Step 4.3: Database Connectivity
```bash
# Test database queries
psql -U squad -d squad_api -h prod-db.example.com -c "SELECT COUNT(*) FROM audit_logs;"
# Expected: Returns count, no errors

# Verify connection pool
curl -s https://api.squad-api.example.com/metrics | grep db_connections
# Expected: Normal pool utilization
```

#### Step 4.4: Provider Integration
```bash
# Test provider calls
curl -X POST https://api.squad-api.example.com/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "agent_id": "code"
  }'
# Expected: 200 OK with response

# Verify all providers
for provider in groq cerebras gemini openrouter; do
  echo "Testing: $provider"
  curl -s https://api.squad-api.example.com/providers | jq ".[] | select(.name==\"$provider\") | .status"
done
# Expected: All "healthy"
```

#### Step 4.5: Resume Traffic
```bash
# Re-enable load balancer
kubectl patch svc squad-api -p '{"spec":{"selector":{"app":"squad-api"}}}'
# OR
aws elbv2 modify-target-group --target-group-arn ... --health-check-enabled=true
# OR
systemctl reload nginx

# Monitor traffic resumption
kubectl top pods -l app=squad-api --containers
# Expected: CPU/Memory returning to baseline

# Watch error rate return to baseline
# Check Prometheus dashboard: error_rate_percentage < 0.1%
```

### Phase 5: Post-Rollback Stabilization (T+5 to T+15 min)

#### Step 5.1: Full Smoke Test Suite
```bash
# Run automated smoke tests
python -m pytest tests/smoke/ -v --tb=short
# Expected: 100% passing

# Manual verification
curl -s https://api.squad-api.example.com/health | jq '.status'
# Expected: "ok"

curl -s https://api.squad-api.example.com/providers | jq '.[] | .name'
# Expected: List of all providers
```

#### Step 5.2: Customer Impact Assessment
```bash
# Check API usage metrics
# Query: requests_per_minute, success_rate
# Expected: Returning to pre-incident baseline

# Review support tickets
# Expected: No new tickets related to deployment

# Check data integrity
# Expected: No corrupted records since rollback
```

#### Step 5.3: Incident Communication
```
#incident-response channel update:

🔄 ROLLBACK COMPLETE

Timeline:
- T+0:00 - Problem detected
- T+1:00 - Rollback approved
- T+3:00 - Rollback complete
- T+5:00 - Verification passed

Current Status:
✅ Error rate < 0.1%
✅ All providers healthy
✅ Database consistent
✅ Traffic normalized

Version: v1.0.0 (rolled back from v1.0.1)
Database: Restored from pre-deploy snapshot
Cache: Flushed and restarted

Next Steps:
1. Incident review (30 min)
2. Root cause analysis
3. Fix implementation
4. Re-deployment (tomorrow after full testing)

Timeline: 📊 [Full incident chart]
Impact: ~500 requests affected, <2min downtime
```

---

## 📋 POST-ROLLBACK PROCEDURE

### Immediate (Within 30 minutes)

#### Step 1: Incident Review
```markdown
## Incident Review - [Timestamp]

**What happened:**
- [Describe issue clearly]
- [Impact scope]
- [User-facing impact]

**How we detected it:**
- [Alert that triggered]
- [Time to detection]

**How we responded:**
- [Timeline of actions]
- [Decision points]

**Resolution:**
- [Rollback completion]
- [Verification time]
```

#### Step 2: Alert Team
```bash
# All-hands message
@channel 📋 Incident Post-Mortem - Squad API Deployment

Incident Duration: 3 minutes
Impact: ~500 requests (0.1% of traffic)
Root Cause: [To be determined]

Post-mortem meeting: 2025-11-13 16:00 UTC
Duration: 30 minutes
Attendees: Engineering, Ops, Product

Agenda:
1. Timeline review (5 min)
2. Root cause analysis (10 min)
3. Prevention measures (10 min)
4. Action items (5 min)
```

### Follow-up (Next 24 hours)

#### Step 3: Root Cause Analysis
```markdown
## Root Cause Analysis

**Problem Statement:**
[Concise description]

**Timeline:**
- T+0: [Event]
- T+1: [Action]
- T+N: [Resolution]

**Root Cause:**
[The "why" behind the issue]

**Contributing Factors:**
1. [Factor 1]
2. [Factor 2]

**Trigger:**
[What caused it to happen now]
```

#### Step 4: Prevention Plan
```markdown
## Prevention Measures

**Process Changes:**
- [ ] Add pre-deployment check for [issue]
- [ ] Improve testing for [scenario]
- [ ] Add monitoring alert for [metric]

**Code Changes:**
- [ ] Fix [bug] in production code
- [ ] Add defensive check for [edge case]
- [ ] Improve error handling for [component]

**Infrastructure Changes:**
- [ ] Add [monitoring/safeguard]
- [ ] Improve [process/automation]

**Timeline:**
- Short-term (< 1 week): [Action items]
- Medium-term (1-4 weeks): [Action items]
- Long-term (1+ month): [Action items]
```

#### Step 5: Create Action Items
```bash
# Jira/GitHub Issues format

[Bug/Improvement] Prevent [issue description]
Story: 9.8.1 - Post-Incident Improvements
Priority: High
Assignee: [Engineer name]
Due Date: 2025-11-16

Description:
- [What happened]
- [What we need to fix]
- [How to verify it's fixed]
- [Testing approach]

Acceptance Criteria:
- [ ] Fix implemented
- [ ] Tests added
- [ ] Code reviewed
- [ ] Deployed to staging
- [ ] Verified in production
```

---

## 🛡️ ROLLBACK SAFEGUARDS

### Automated Rollback Triggers (Optional Advanced)
```yaml
# .github/workflows/auto-rollback.yml
name: Auto Rollback on High Error Rate

on:
  schedule:
    - cron: '*/1 * * * *'  # Every 1 minute

jobs:
  check-health:
    runs-on: ubuntu-latest
    steps:
      - name: Check error rate
        run: |
          ERROR_RATE=$(curl -s https://metrics.example.com/api/v1/query?query=rate(errors[5m]))
          if [ "$ERROR_RATE" > "0.01" ]; then
            echo "High error rate detected: $ERROR_RATE"
            ./scripts/rollback.sh
            ./scripts/alert.sh
          fi
```

### Rollback Approval Gates
```
Automatic Rollback Decision Tree:

Error Rate > 1% for 2+ minutes?
├─ YES → Rollback approved (automatic)
└─ NO  → Manual decision required

All Providers Down?
├─ YES → Rollback approved (automatic)
└─ NO  → Check error rate

Database Unavailable?
├─ YES → Rollback approved (automatic)
└─ NO  → Escalate to on-call

Manual Approval Required:
- Incident Lead: [Slack reaction]
- Ops Lead: [Slack reaction]
- Security (if applicable): [Slack reaction]
```

---

## 📊 SUCCESS CRITERIA

### Rollback Successful If:
- ✅ All health checks passing
- ✅ Error rate < 0.1%
- ✅ P95 latency < 2s
- ✅ >99% request success rate
- ✅ Database consistent
- ✅ No PII exposed in logs
- ✅ Monitoring dashboards stable

### Rollback Failed If:
- ❌ Error rate still high (>0.5%)
- ❌ Database restore incomplete
- ❌ Services not starting
- ❌ Network connectivity lost
- ❌ → Escalate to incident commander

---

## 🆘 WHEN ROLLBACK FAILS

### If Initial Rollback Unsuccessful
```
1. STOP all remediation attempts
2. Declare P1 incident
3. Call incident commander
4. Call database administrator
5. Assemble emergency response team
6. Contact Cloud provider support

Do NOT:
- ❌ Try multiple rollback attempts without assessment
- ❌ Keep system running with data corruption
- ❌ Make unreviewed database changes
- ❌ Restart services without investigation
```

### Escalation Contacts
| Level | Role | Contact | Response |
|-------|------|---------|----------|
| 1 | On-Call Engineer | [Phone] | 5 min |
| 2 | Incident Commander | [Phone] | 10 min |
| 3 | DBA Lead | [Phone] | 15 min |
| 4 | VP Engineering | [Phone] | 30 min |
| 5 | Cloud Provider Support | [Ticket] | 1 hour |

---

**Generated: 2025-11-13**
**Story: 9.8 - Go-Live Procedure (Part 2/4)**
**Next: Incident Response Playbook, Final Validation**
