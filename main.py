#!/usr/bin/env python3
"""
Main orchestrator script for the AI Recruiter Copilot.
This script serves as the entry point to execute the recruitment workflow.
"""

from agents.workflows.recruitment_flow import main_workflow


if __name__ == "__main__":
    main_workflow()
