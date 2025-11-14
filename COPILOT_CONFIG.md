# Copilot Configuration - Disable Context Summarization

## Problem
Copilot (Claude/Haiku) freezes when attempting to summarize very large conversations (200+ messages).

## Solution
This config tells Copilot to NEVER attempt conversation summarization.

## Rules for Copilot

**DO NOT:**
- Attempt to summarize conversation history
- Try to compress past messages
- Create context snapshots
- Batch-process multiple messages
- Attempt token counting of entire conversation

**DO:**
- Work with what's explicitly given
- Process one request at a time
- Skip context compression
- Move forward with new tasks
- Ask for clarification if needed

## Implementation

If conversation gets too large:
1. **Split into new conversation** (refresh)
2. **Or** paste only relevant context
3. **Or** create new chat for new topic

## Expected Behavior

✅ Quick responses
✅ No timeouts
✅ No "Summarizing..." freezes
✅ Smooth handoffs to local LLM when needed
