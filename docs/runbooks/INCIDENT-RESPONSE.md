# Incident Response Playbook - Story 9.8
# Squad API Emergency Response Guide
# Date: 2025-11-13 | Epic 9: Production Readiness

## 📞 INCIDENT SEVERITY LEVELS

### P1 - Critical (Immediate Response)
- **Response Time:** <5 minutes
- **Escalation:** All-hands on deck
- **Examples:**
  - Complete service outage
  - Data corruption detected
  - Security breach
  - All providers failing
  - Database unavailable
- **Decision Window:** 2 minutes (escalate or remediate)
- **Comms:** Every 5 minutes

### P2 - High (Urgent Response)
- **Response Time:** <15 minutes
- **Escalation:** Engineering lead + On-call
- **Examples:**
  - >50% of users affected
  - Error rate >1% for 10+ minutes
  - >50% providers unavailable
  - PII potentially exposed
- **Decision Window:** 5 minutes
- **Comms:** Every 10 minutes

### P3 - Medium (Prompt Response)
- **Response Time:** <1 hour
- **Escalation:** Engineering team
- **Examples:**
  - <50% of users affected
  - Error rate >0.5% for 5+ minutes
  - Degraded performance (P95 latency >5s)
  - Non-critical feature broken
- **Decision Window:** 10 minutes
- **Comms:** Every 30 minutes

### P4 - Low (Routine Response)
- **Response Time:** <4 hours
- **Escalation:** Assigned engineer
- **Examples:**
  - Minor UI issues
  - Low-impact feature requests
  - Performance optimization opportunity
- **Decision Window:** None (no urgency)
- **Comms:** Once resolved

---

## 🚨 INCIDENT COMMANDER ROLE

### Responsibilities
```
INCIDENT COMMANDER
│
├─ Declare incident severity
├─ Assemble response team
├─ Maintain incident timeline
├─ Make go/no-go decisions (escalate/rollback)
├─ Lead war room communications
├─ Track action items
└─ Post-incident review

NOT Responsible For:
├─ Technical troubleshooting (assign to engineers)
├─ Customer communications (assign to PM/support)
├─ Management updates (assign to leadership)
```

### On-Call Rotation
```
Monday-Friday:
  00:00-08:00 UTC: [Engineer 1]
  08:00-16:00 UTC: [Engineer 2]
  16:00-00:00 UTC: [Engineer 3]

Weekends & Holidays:
  Dedicated on-call (24/7)
  Backup on-call (2nd person)

Handoff:
- 30 min overlap for context sharing
- Previous on-call available for 1 hour after shift
- All incidents logged in incident tracking system
```

---

## 🔴 P1 INCIDENT RESPONSE - CRITICAL

### T+0:00 - Problem Detected
```
Triggers:
- Alert fires (automated monitoring)
- User report (support@squad-api.example.com)
- Internal observation (team member)

Immediate Actions:
1. ✅ Declare incident in #incident-response Slack channel
   "🚨 P1 INCIDENT DECLARED: [Brief description]"

2. ✅ Trigger on-call engineer
   PagerDuty / Slack DM: "P1 incident, check #incident-response"

3. ✅ Assemble response team (simultaneously)
   - Incident Commander
   - Primary Engineer
   - Database Administrator (if DB issue)
   - Operations Lead

4. ✅ Document initial state
   - Timestamp: 2025-11-13T14:30:00Z
   - Issue: [Clear description]
   - Detected by: [Alert name or person]
   - Affected users: [Percentage/count]
   - Service status: Down/Degraded/Slow
```

### T+1:00 - Assessment
```
Incident Commander Leads:
1. Gather facts
   - What component is affected? (API/DB/Providers/Cache)
   - When did it start? (exact timestamp)
   - What changed? (deployment/traffic spike/external)
   - Customers affected? (percentage)
   - Revenue impact? (estimate)

2. Get status from each team
   - Engineering: Can we fix? (rollback/patch/workaround)
   - Ops: Database health? Cache status?
   - Database: Backup available? Restore time?
   - Security: Data leak potential?

3. Assess severity
   - Is this truly P1? (Escalate/Downgrade if needed)
   - Estimated time to resolution (TTR)
   - Acceptable downtime window

4. Make initial decision
   A) Rollback? (if recent deployment)
   B) Scale? (if load/capacity issue)
   C) Patch? (if bug fix available)
   D) Failover? (if server/region issue)
   E) Escalate? (if beyond team capability)
```

### T+2:00 - Action Execution
```
Chosen Path Execution:

IF Rollback Decision:
→ Execute ROLLBACK-PROCEDURE.md
→ Follow Phase 1-4 steps
→ Target TTR: <3 minutes

IF Scale Decision:
→ kubectl scale deployment squad-api --replicas=10
→ Add servers if at capacity
→ Monitor metrics during scale-up
→ Target TTR: <5 minutes

IF Patch Decision:
→ Apply bug fix with careful rollout
→ Canary: 10% traffic
→ Monitor: 3 minutes
→ Full rollout if successful
→ Target TTR: <10 minutes

IF Failover Decision:
→ DNS cutover to backup region
→ Verify all components responsive
→ Monitor error rates
→ Target TTR: <5 minutes

Parallel Actions:
- Comms: Notify stakeholders every 2 min
- Monitoring: Watch metrics for resolution
- Logging: Record all actions taken
```

### T+5:00 - Stabilization
```
If Issue Resolved:
✅ Confirm all metrics returned to baseline
✅ Run full smoke test suite
✅ Verify no data corruption
✅ Notify all stakeholders

If Issue Persistent:
❌ Declare escalation to VP Engineering
❌ Involve cloud provider support (if needed)
❌ Prepare for extended incident
❌ Switch to "Extended Response" mode
```

### T+30:00 - Post-Incident
```
1. Stop active incident response
2. Create incident summary
3. Schedule post-mortem (within 24 hours)
4. Document lessons learned
5. Create action items
6. Assign owners and due dates
```

---

## 🟠 P2 INCIDENT RESPONSE - HIGH

### T+0:00 - Detection & Acknowledgment
```
Alert Fired:
- Error rate > 1% OR
- Latency P95 > 5s OR
- >50% requests failing

Response:
1. On-call engineer acknowledges alert (PagerDuty)
2. Post in #incidents channel with assessment
3. Notify team lead if affecting customer
```

### T+0-15:00 - Investigation
```
Primary Engineer Investigates:
- ✅ Check last deployment (git log -1)
- ✅ Compare before/after metrics
- ✅ Review error logs
- ✅ Check provider status
- ✅ Query database performance
- ✅ Review recent configuration changes

Assessment Options:
A) It's a P1 → Escalate to P1 flow
B) Self-healing → Wait and monitor (set alert for P1 threshold)
C) Requires rollback → Initiate rollback (if deployment related)
D) Requires scale → Scale up services
E) Requires patch → Apply fix after assessment
```

### T+15-60:00 - Resolution
```
Resolution Paths:
- Rollback (if deployment caused it)
- Scale (if capacity issue)
- Patch (if application bug)
- Configuration (if misconfigured)
- Wait (if transient issue resolving)

Success Criteria:
✅ Error rate < 0.5%
✅ Latency P95 < 3s
✅ >99% success rate
✅ No further alerts
✅ Customer notification sent (if needed)
```

---

## 🟡 P3 INCIDENT RESPONSE - MEDIUM

### T+0-60:00 - Normal Investigation
```
Process:
1. Acknowledge alert
2. Assess urgency (true P3?)
3. If P1/P2 → Escalate
4. Investigate root cause
5. Plan fix
6. Implement and test
7. Deploy during office hours
8. Document lessons
```

### Resolution
```
Options:
- Schedule fix for next sprint
- Implement urgent patch
- Monitor and watch for escalation
- Document workaround for users
```

---

## 📊 INCIDENT COMMUNICATIONS TEMPLATE

### Initial Declaration (T+0)
```
Channel: #incident-response
Audience: All engineers

🚨 INCIDENT DECLARED

Severity: P[1-4]
Component: [API/Database/Providers/Cache]
Impact: [Description of what's broken]
Customers Affected: [Estimate: %]
Time Started: [Exact UTC timestamp]

Incident Commander: @[name]
Status Page: [Link to status.example.com]

Next update: [Time] UTC
```

### 5-Minute Update
```
📊 INCIDENT UPDATE - [Time]

Status: Investigating / Resolving / Resolved
Time Elapsed: [Duration]
Current Impact: [Description]
Work In Progress: [What we're doing]
Estimated Time to Resolution: [Estimate]

Actions Taken:
- [Action 1] completed
- [Action 2] in progress
- [Action 3] planned

Next Update: [Time] UTC
```

### Resolution Announcement
```
✅ INCIDENT RESOLVED - [Time]

Issue: [What went wrong]
Duration: [Total time]
Impact: [How many users affected, revenue loss]
Resolution: [What we did to fix it]

Details:
- Start Time: [UTC]
- Detection Time: [UTC]
- Resolution Time: [UTC]
- Mean Time To Detection: [MTTD]
- Mean Time To Resolution: [MTTR]

Timeline:
T+0:00 - [Initial alert]
T+1:30 - [Decision made]
T+3:45 - [Issue resolved]

Post-Mortem: [Date/Time] UTC
Action Items: [GitHub/Jira links]

We apologize for the disruption.
```

### Customer Communication (Optional)
```
From: support@squad-api.example.com
To: [Affected Customers]
Subject: Incident Report - [Date]

We experienced an incident on [Date] at [Time] UTC.

What Happened:
[Plain language explanation of issue]

Impact:
- Duration: [X] minutes
- Services Affected: [List]
- Percentage of Requests: [X]%

Root Cause:
[Explanation]

What We Did:
- [Action 1]
- [Action 2]
- [Action 3]

Prevention:
[How we'll prevent it in future]

We apologize for the impact to your service.
If you have questions, please contact support@squad-api.example.com

Squad API Team
```

---

## 🛠️ INCIDENT TROUBLESHOOTING QUICK REFERENCE

### High Error Rate (>1%)
```bash
# Check logs for errors
kubectl logs deployment/squad-api -f --tail=100 | grep ERROR

# Check metrics
curl metrics.example.com/api/v1/query?query=http_requests_total{status="500"}

# Possible causes:
1. Recent deployment → Rollback
2. Database issue → Check connectivity
3. Provider issue → Check provider status
4. Configuration issue → Review recent changes
```

### High Latency (P95 >5s)
```bash
# Check performance metrics
curl metrics.example.com/api/v1/query?query=http_request_duration_seconds

# Check database performance
psql -U squad -d squad_api -c "SHOW statement_timeout;"
SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;

# Possible causes:
1. Database slow → Check query performance
2. External provider slow → Check latency
3. Cache miss → Invalidate and repopulate
4. N+1 queries → Check application code
```

### Database Connection Issues
```bash
# Check connection pool
curl metrics.example.com/api/v1/query?query=db_connection_pool_size

# Check database status
pg_isready -h prod-db.example.com -p 5432

# Possible causes:
1. Connection limit reached → Scale pool
2. Database down → Check database health
3. Network issue → Check connectivity
4. Credentials wrong → Verify ENV variables
```

### All Providers Failing
```bash
# Check provider status endpoint
curl https://api.squad-api.example.com/providers

# Check recent API key changes
grep -r "PROVIDER" .env | head

# Test each provider manually
curl -X POST https://api.groq.example.com/v1/chat \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Possible causes:
1. API keys expired → Rotate keys
2. Provider service down → Check provider status page
3. Rate limiting → Check rate limit headers
4. Network firewall → Check egress rules
```

### Memory/CPU Issues
```bash
# Check resource usage
kubectl top pods -l app=squad-api

# Possible causes:
1. Memory leak → Restart pods
2. High concurrency → Scale horizontally
3. Large response → Check response sizes
4. Inefficient query → Optimize query
```

---

## 📋 POST-INCIDENT PROCEDURES

### Immediate (0-30 min)
```
1. ✅ Incident closed
2. ✅ Metrics returned to baseline
3. ✅ War room dissolved
4. ✅ Initial incident summary created
5. ✅ All team members notified of resolution
6. ✅ Status page updated to "Operational"
```

### Short-term (1-4 hours)
```
1. ✅ Draft incident timeline
2. ✅ Collect logs and metrics
3. ✅ Interview primary engineers
4. ✅ Identify root cause
5. ✅ Create action items (GitHub/Jira)
6. ✅ Assign owners
```

### Follow-up (Next business day)
```
1. ✅ Post-mortem meeting (30-45 min)
   - Timeline review
   - Root cause analysis
   - Contributing factors
   - Action items (prevention)

2. ✅ Create preventing action items
   - Process improvements
   - Monitoring improvements
   - Testing improvements
   - Documentation updates

3. ✅ Update runbooks based on learnings

4. ✅ Team training/discussion on findings
```

---

## 📞 ESCALATION MATRIX

```
Issue Type              | Severity | Escalate To           | When
─────────────────────────────────────────────────────────────────────
Deploy failure         | P1       | VP Engineering        | >5 min unresolved
Database corruption    | P1       | DBA + VP Engineering  | Immediate
Security breach        | P1       | CISO + VP Engineering | Immediate
Complete outage        | P1       | All hands              | >2 min unresolved
Partial outage         | P2       | Engineering Lead      | >15 min unresolved
Performance degr.      | P2       | Engineering Lead      | >30 min unresolved
Bug fix needed         | P3       | Team Lead             | Assign engineer
Feature request        | P4       | Product Manager       | Next sprint
```

---

## ✅ INCIDENT RESPONSE CHECKLIST

### During Incident
- [ ] Severity declared
- [ ] Incident commander assigned
- [ ] War room opened
- [ ] Initial assessment done
- [ ] Action plan created
- [ ] Updates sent every 5 minutes
- [ ] Decision made (rollback/patch/scale/escalate)
- [ ] Action executed
- [ ] Issue resolved

### After Incident
- [ ] Incident closed
- [ ] Timeline documented
- [ ] Root cause identified
- [ ] Action items created
- [ ] Post-mortem scheduled
- [ ] Customers notified
- [ ] Status page updated
- [ ] Team debriefed

---

**Generated: 2025-11-13**
**Story: 9.8 - Go-Live Procedure (Part 3/4)**
**Next: Final Validation & Sign-Off**
