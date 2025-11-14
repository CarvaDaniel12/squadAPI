# Test Design - Epic 1: Agent Transformation Engine

**Designer:** Murat (Master Test Architect)  
**Date:** 2025-11-13  
**Epic:** Epic 1 - Agent Transformation Engine  
**Stories:** 1.1-1.16

---

## Test Coverage Summary

**Existing Tests:** 32 total
- Unit: 29 tests ✅
- Integration: 3 tests ✅
- E2E: 0 tests ❌
- Load: 0 tests ❌

**Coverage:** 27-54% (varies by test scope)

---

## Additional Test Scenarios Needed

### Priority 1: Critical Security Tests

**Tool Executor Security** (Story 1.14)

```python
# tests/unit/test_tools/test_executor.py

class TestToolExecutorSecurity:
    """Security validation for tool executor"""
    
    @pytest.mark.unit
    async def test_path_traversal_blocked():
        """SECURITY: Block directory traversal attacks"""
        executor = ToolExecutor()
        
        # Test various traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            ".bmad/../../../secrets.txt",
            "/etc/shadow"
        ]
        
        for path in malicious_paths:
            with pytest.raises(SecurityError, match="traversal"):
                await executor.execute("load_file", {"path": path})
    
    @pytest.mark.unit
    async def test_whitelist_enforcement():
        """SECURITY: Only whitelisted paths allowed"""
        executor = ToolExecutor()
        
        # Valid paths
        valid = [
            ".bmad/bmm/agents/analyst.md",
            "docs/PRD.md",
            "config/rate_limits.yaml"
        ]
        
        for path in valid:
            # Should not raise
            try:
                result = await executor.execute("load_file", {"path": path})
            except FileNotFoundError:
                pass  # File may not exist, OK
        
        # Invalid paths
        invalid = [
            "src/main.py",  # Not in whitelist
            "requirements.txt",  # Not in whitelist
            ".env"  # Security sensitive
        ]
        
        for path in invalid:
            with pytest.raises(SecurityError, match="whitelist"):
                await executor.execute("load_file", {"path": path})
    
    @pytest.mark.unit
    async def test_write_whitelist_stricter():
        """SECURITY: Write whitelist more restrictive than read"""
        executor = ToolExecutor()
        
        # Can READ from .bmad/ but cannot WRITE
        # Can only WRITE to docs/ and .bmad-ephemeral/
        
        # Should fail (read-only path)
        with pytest.raises(SecurityError):
            await executor.execute("save_file", {
                "path": ".bmad/test.txt",
                "content": "test"
            })
        
        # Should succeed
        result = await executor.execute("save_file", {
            "path": "docs/test-output.md",
            "content": "# Test"
        })
        assert "saved successfully" in result.lower()
```

**Priority:** 🔴 CRITICAL  
**Effort:** 2-3 hours  
**Must Complete:** Before Epic 3 (real LLM providers)

---

### Priority 2: API Contract Tests

**API Endpoints** (Stories 1.7-1.8)

```python
# tests/integration/test_api_contracts.py

class TestAgentExecutionAPI:
    """Contract tests for agent execution endpoint"""
    
    @pytest.mark.integration
    async def test_execute_agent_success_response():
        """Validate response schema matches PRD specification"""
        from fastapi.testclient import TestClient
        from src.main import app
        
        client = TestClient(app)
        
        response = client.post("/api/v1/agent/execute", json={
            "agent": "analyst",
            "task": "Test task",
            "user_id": "test"
        })
        
        # Validate status code
        assert response.status_code == 200
        
        # Validate response schema
        data = response.json()
        assert "agent" in data
        assert "agent_name" in data
        assert "provider" in data
        assert "model" in data
        assert "response" in data
        assert "metadata" in data
        
        # Validate metadata schema
        metadata = data["metadata"]
        assert "latency_ms" in metadata
        assert "tokens_input" in metadata
        assert "tokens_output" in metadata
        assert "fallback_used" in metadata
    
    @pytest.mark.integration
    async def test_execute_agent_not_found_error():
        """Validate 404 error format for missing agent"""
        client = TestClient(app)
        
        response = client.post("/api/v1/agent/execute", json={
            "agent": "nonexistent",
            "task": "Test"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "agent_not_found"
        assert "available_agents" in data
    
    @pytest.mark.integration
    async def test_list_agents_response():
        """Validate agents list endpoint"""
        client = TestClient(app)
        
        response = client.get("/api/v1/agents/available")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "agents" in data
        assert data["count"] >= 8  # 8 BMad agents
```

**Priority:** 🟡 HIGH  
**Effort:** 2 hours  
**Benefit:** Contract validation, API stability

---

### Priority 3: Edge Cases

**Context Window Edge Cases**

```python
# tests/unit/test_agents/test_context_edge_cases.py

@pytest.mark.unit
def test_trim_messages_exactly_at_limit():
    """Test when messages exactly fill context window"""
    manager = ContextWindowManager(max_context=1000)
    
    # Create messages that total exactly 1000 tokens
    messages = create_messages_with_exact_tokens(1000)
    
    trimmed = manager.trim_messages(messages, "", max_tokens=1000)
    
    # Should not trim
    assert len(trimmed) == len(messages)

@pytest.mark.unit
def test_trim_messages_single_huge_message():
    """Test when single message exceeds context"""
    manager = ContextWindowManager(max_context=1000)
    
    # Single message larger than context
    huge_message = {"role": "user", "content": "x" * 10000}
    messages = [huge_message]
    
    # Should keep at least system + user (even if over)
    trimmed = manager.trim_messages(messages, "system", max_tokens=1000)
    
    # Should return at minimum: system + user (even if overflowing)
    assert len(trimmed) >= 1
```

**Priority:** 🟢 MEDIUM  
**Effort:** 1 hour

---

### Priority 4: Performance Baseline Tests

**Latency Benchmarks** (for Epic 5)

```python
# tests/integration/test_performance_baseline.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_execution_latency_baseline():
    """Establish baseline latency (no LLM call)"""
    import time
    
    orchestrator = create_test_orchestrator()
    
    request = AgentExecutionRequest(
        agent="analyst",
        task="Quick test",
        user_id="perf_test"
    )
    
    start = time.time()
    response = await orchestrator.execute(request)
    latency = (time.time() - start) * 1000  # ms
    
    # Without LLM call, should be <50ms
    assert latency < 50, f"Baseline latency too high: {latency}ms"
    
    print(f"Baseline latency: {latency:.2f}ms")
```

**Priority:** 🟢 MEDIUM  
**Benefit:** Performance regression detection

---

## Test Scenarios: Missing Coverage

### Epic 0 (Foundation) - Missing Tests

**Infrastructure Tests:**
- [ ] Docker Compose startup test
- [ ] Redis connection test
- [ ] PostgreSQL connection test
- [ ] Prometheus scraping test
- [ ] Grafana datasource test

**Status:** ⚠️ Manual testing only (automated tests recommended for CI/CD)

---

### Epic 1 (Agent Transformation) - Missing Tests

**High Priority:**
1. ✅ Parser - Well tested (7 tests)
2. ✅ Models - Well tested (embedded in other tests)
3. ⚠️ Loader - Needs Redis integration tests
4. ✅ Prompt Builder - Excellent (10 tests)
5. ✅ Conversation - Excellent (7 tests)
6. ⚠️ Router - Basic coverage, needs error paths
7. ⚠️ Orchestrator - Good (3 integration tests), needs edge cases
8. ✅ List Endpoint - Covered in integration
9. ❌ Context Window - **NOT TESTED** (0% coverage)
10. ❌ Hot-Reload - **NOT TESTED** (0% coverage)
11. ✅ Integration Test - Good (3 tests)
12. ✅ Error Handling - Basic coverage
13. ❌ Tool Definitions - **NOT TESTED**
14. ❌ Tool Executor - **NOT TESTED** (SECURITY CRITICAL!)
15. ❌ Multi-Turn Loop - Not implemented yet (Epic 3 dependency)
16. ❌ Web Search - Stub only

---

## Action Plan

### Before Epic 3 (Providers)

**Must Do:**
- [ ] **Add tool executor security tests** (2 hours) 🔴
- [ ] **Add API contract tests** (2 hours) 🟡

**Should Do:**
- [ ] Add context window tests (1 hour)
- [ ] Add router error path tests (1 hour)

**Total Effort:** ~6 hours

### During Epic 3

- [ ] Test real provider integration
- [ ] Test rate limiting (Epic 2)
- [ ] Test fallback chains (Epic 4)

### Before Production (Epic 9)

- [ ] E2E tests (Story 8.7)
- [ ] Load tests (Story 9.6)
- [ ] Security tests (Story 9.7)

---

## Conclusion

**Test Quality:** ✅ EXCELLENT for implemented features  
**Test Coverage:** ⚠️ GAPS in tools, API, infrastructure  
**Test Design:** ✅ SOUND (proper isolation, fixtures, async)  

**Recommendation:** 
1. Add **tool executor security tests** NOW (2 hours)
2. Add **API contract tests** (2 hours)
3. Then proceed to Epic 3

**Overall QA Verdict:** ✅ **APPROVED** with action items

---

**Generated:** 2025-11-13 by TEA Agent (Murat)

