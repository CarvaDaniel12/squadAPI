"""
Unit Tests for Tool Executor
QA Action Item 1: Tool Executor Security Tests
"""

import pytest
from pathlib import Path
from src.tools.executor import ToolExecutor, SecurityError


class TestToolExecutorSecurity:
    """Security validation for tool executor"""
    
    @pytest.fixture
    def executor(self):
        """Create executor instance"""
        return ToolExecutor(project_root=".")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, executor):
        """SECURITY: Block directory traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            ".bmad/../../../secrets.txt",
            "/etc/shadow",
            "docs/../../.env"
        ]
        
        for path in malicious_paths:
            with pytest.raises(SecurityError, match="traversal"):
                await executor.execute("load_file", {"path": path})
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_read_whitelist_enforcement(self, executor):
        """SECURITY: Only whitelisted paths allowed for reading"""
        # Valid paths (in whitelist: .bmad/, docs/, config/)
        valid_read_paths = [
            ".bmad/bmm/agents/analyst.md",
            "docs/PRD.md",
            "config/prometheus.yml"
        ]
        
        for path in valid_read_paths:
            # Should not raise SecurityError (may raise FileNotFoundError if file doesn't exist)
            try:
                result = await executor.execute("load_file", {"path": path})
                assert isinstance(result, str)
            except FileNotFoundError:
                pass  # OK - file doesn't exist, but path validation passed
        
        # Invalid paths (NOT in read whitelist)
        invalid_read_paths = [
            "src/main.py",
            "requirements.txt",
            ".env",
            "venv/Scripts/python.exe",
            "tests/unit/test.py"
        ]
        
        for path in invalid_read_paths:
            with pytest.raises(SecurityError, match="whitelist"):
                await executor.execute("load_file", {"path": path})
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_write_whitelist_stricter_than_read(self, executor):
        """SECURITY: Write whitelist more restrictive than read"""
        # Can READ from .bmad/ but CANNOT WRITE
        with pytest.raises(SecurityError, match="whitelist"):
            await executor.execute("save_file", {
                "path": ".bmad/test.txt",
                "content": "malicious"
            })
        
        # Can READ from config/ but CANNOT WRITE
        with pytest.raises(SecurityError, match="whitelist"):
            await executor.execute("save_file", {
                "path": "config/malicious.yaml",
                "content": "attack"
            })
        
        # Can WRITE to docs/ (whitelisted for write)
        result = await executor.execute("save_file", {
            "path": "docs/test-output.md",
            "content": "# Test Output"
        })
        assert "saved successfully" in result.lower()
        
        # Cleanup
        Path("docs/test-output.md").unlink(missing_ok=True)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_absolute_path_blocked(self, executor):
        """SECURITY: Absolute paths are blocked"""
        absolute_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32\\config",
            "/home/user/.ssh/id_rsa"
        ]
        
        for path in absolute_paths:
            with pytest.raises(SecurityError, match="traversal"):
                await executor.execute("load_file", {"path": path})


class TestToolExecutorFunctionality:
    """Functional tests for tool executor"""
    
    @pytest.fixture
    def executor(self):
        """Create executor instance"""
        return ToolExecutor(project_root=".")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_file_success(self, executor):
        """Test loading a valid file"""
        # Load real file
        result = await executor.execute("load_file", {
            "path": ".bmad/bmm/agents/analyst.md"
        })
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Mary" in result or "analyst" in result.lower()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_file_not_found(self, executor):
        """Test loading non-existent file"""
        with pytest.raises(FileNotFoundError):
            await executor.execute("load_file", {
                "path": "docs/nonexistent-file.md"
            })
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_file_creates_parent_dirs(self, executor):
        """Test save_file creates parent directories"""
        test_path = "docs/subdir/test-file.md"
        
        # Save file
        result = await executor.execute("save_file", {
            "path": test_path,
            "content": "# Test Content"
        })
        
        assert "saved successfully" in result.lower()
        assert Path(test_path).exists()
        
        # Cleanup
        Path(test_path).unlink()
        Path(test_path).parent.rmdir()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_directory_success(self, executor):
        """Test listing directory contents"""
        result = await executor.execute("list_directory", {
            "path": "docs"
        })
        
        assert isinstance(result, str)
        assert "PRD.md" in result or "architecture.md" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_directory_not_found(self, executor):
        """Test listing non-existent directory"""
        with pytest.raises(FileNotFoundError):
            await executor.execute("list_directory", {
                "path": "docs/nonexistent-dir"
            })
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_workflow_status(self, executor):
        """Test workflow status update"""
        result = await executor.execute("update_workflow_status", {
            "workflow": "research",
            "output_file": "docs/research-2025-11-13.md"
        })
        
        assert "research" in result.lower()
        assert "complete" in result.lower()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_web_search_stub(self, executor):
        """Test web search (stub implementation)"""
        result = await executor.execute("web_search", {
            "query": "Python async best practices"
        })
        
        assert isinstance(result, str)
        assert "Python async best practices" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, executor):
        """Test calling unknown tool raises ValueError"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await executor.execute("unknown_tool_xyz", {})


class TestToolExecutorEdgeCases:
    """Edge case tests for tool executor"""
    
    @pytest.fixture
    def executor(self):
        return ToolExecutor(project_root=".")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_file_content(self, executor):
        """Test saving empty file"""
        result = await executor.execute("save_file", {
            "path": "docs/empty-test.md",
            "content": ""
        })
        
        assert "saved successfully" in result.lower()
        assert Path("docs/empty-test.md").exists()
        
        # Cleanup
        Path("docs/empty-test.md").unlink()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_very_long_path(self, executor):
        """Test very long but valid path"""
        long_path = "docs/" + "a" * 200 + ".md"
        
        # Should not raise SecurityError (but may fail for other reasons)
        try:
            result = await executor.execute("save_file", {
                "path": long_path,
                "content": "test"
            })
            # Cleanup if succeeded
            Path(long_path).unlink(missing_ok=True)
        except Exception as e:
            # Any error except SecurityError is OK
            assert not isinstance(e, SecurityError)

