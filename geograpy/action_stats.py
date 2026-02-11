"""
Created on 2026-02-11

@author: wf
"""


class ActionStats:
    """Helper class to track success rates of actions."""

    def __init__(self):
        self.success_count = 0
        self.total_count = 0
        self.current = None

    def add(self, is_success: bool):
        """adds a single result."""
        self.current = is_success
        self.total_count += 1
        if is_success:
            self.success_count += 1

    @property
    def ratio(self) -> float:
        """Returns the success/total ratio."""
        ratio = self.success_count / self.total_count if self.total_count > 0 else 0.0
        return ratio

    def state(self, success_msg, fail_msg) -> str:
        """
        return the current state
        """
        if self.current:
            msg = f"✅{success_msg}"
        else:
            msg = f"❌: {fail_msg}"
        return msg

    def __str__(self):
        """Returns the formatted summary string."""
        marker = "❌ " if self.success_count < self.total_count else "✅"
        text = f"{marker}:{self.success_count}/{self.total_count} available"
        return text
