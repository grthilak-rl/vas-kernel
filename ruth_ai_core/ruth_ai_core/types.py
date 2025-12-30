"""
Phase 3.1 – Stream Agent Internal State Model

This module defines the core types for Ruth AI Core Service.

PHASE 3.1 SCOPE:
- AgentState enum (lifecycle states)
- No execution logic
- No external dependencies
"""

from enum import Enum


class AgentState(Enum):
    """
    Stream Agent lifecycle states.

    CREATED: Agent initialized but not yet started
    RUNNING: Agent actively managing subscriptions
    STOPPED: Agent terminated, no longer processing

    State transitions:
    - CREATED -> RUNNING (via start())
    - RUNNING -> STOPPED (via stop())

    No other transitions are valid.
    """
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
