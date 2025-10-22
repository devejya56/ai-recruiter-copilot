#!/usr/bin/env python3
"""
Main orchestrator script for the AI Recruiter Copilot.
This script orchestrates the complete recruitment workflow:
1. Initialize AutomationAgent
2. Parse candidates from Gmail resumes
3. For each candidate: schedule interviews and update status
4. Print results with error handling
"""
import sys
import traceback
from typing import List, Dict, Any

from agents.automation_agent import AutomationAgent


def main():
    """
    Main orchestration function that runs the complete recruitment workflow.
    """
    print("=== AI Recruiter Copilot Started ===")
    
    try:
        # Step 1: Initialize AutomationAgent
        print("\n[Step 1] Initializing AutomationAgent...")
        automation_agent = AutomationAgent()
        print("✓ AutomationAgent initialized successfully")
        
        # Step 2: Parse candidates from Gmail resumes
        print("\n[Step 2] Parsing Gmail resumes...")
        candidates = automation_agent.parse_gmail_resumes()
        
        if not candidates:
            print("⚠️  No candidates found in Gmail resumes")
            return
        
        print(f"✓ Found {len(candidates)} candidates")
        
        # Step 3: For each candidate, schedule interviews and update status
        print("\n[Step 3] Processing candidates...")
        for i, candidate in enumerate(candidates, 1):
            print(f"\n--- Processing Candidate {i}/{len(candidates)} ---")
            try:
                # Print candidate info using attribute access
                name = getattr(candidate, 'name', None) or 'Unknown'
                email = getattr(candidate, 'email', None) or 'No email'
                print(f"  Name: {name}")
                print(f"  Email: {email}")
                
                # Schedule interview
                print("  → Scheduling interview...")
                result = automation_agent.schedule_and_notify(candidate)
                
                if result:
                    print("  ✓ Interview scheduled successfully")
                else:
                    print("  ⚠️  Failed to schedule interview")
                    
            except Exception as e:
                # Use attribute access for error messages too
                name = getattr(candidate, 'name', f'Candidate {i}')
                email = getattr(candidate, 'email', '')
                print(f"  ✗ Error processing candidate {name} ({email}): {str(e)}")
                traceback.print_exc()
                continue
        
        print("\n=== AI Recruiter Copilot Finished ===")
        
    except Exception as e:
        print(f"\n✗ Fatal error in main workflow: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
