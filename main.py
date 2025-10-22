#!/usr/bin/env python3
"""
Main orchestrator script for the AI Recruiter Copilot.
This script orchestrates the complete recruitment workflow:
1. Initialize AutomationAgent
2. Parse candidates from Gmail resumes
3. For each candidate: schedule interviews and update status
4. Print results with error handling
"""

# Load environment variables FIRST, before any other imports that may use them
from dotenv import load_dotenv
import os

load_dotenv()

spreadsheet_id = os.getenv("SPREADSHEET_ID")

# Debug print to verify SPREADSHEET_ID is loaded
print("Loaded Spreadsheet ID:", os.getenv("SPREADSHEET_ID"))

import sys
import traceback
from typing import List, Dict, Any
from datetime import datetime, timedelta
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
        
        # Step 3: For each candidate, schedule interview and update status
        print("\n[Step 3] Processing candidates...")
        for i, candidate in enumerate(candidates, 1):
            try:
                # Use attribute access with getattr for safer access
                name = getattr(candidate, 'name', f'Candidate {i}')
                email = getattr(candidate, 'email', '')
                
                print(f"\n--- Processing Candidate {i}/{len(candidates)}: {name} ({email}) ---")
                
                # Step 3.1: Schedule interview in calendar
                print("  → Scheduling interview in calendar...")
                try:
                    # Calculate interview date (7 days from now)
                    interview_date = datetime.now() + timedelta(days=7)
                    interview_date_str = interview_date.strftime("%Y-%m-%d %H:%M")
                    
                    schedule_result = automation_agent.schedule_interview_in_calendar(
                        candidate_name=name,
                        candidate_email=email,
                        interview_date=interview_date_str
                    )
                    
                    # Step 3.2: Print success/fail message for interview scheduling
                    if schedule_result:
                        print(f"  ✓ Interview scheduled successfully for {interview_date_str}")
                        scheduling_status = "Scheduled"
                    else:
                        print("  ⚠️  Failed to schedule interview in calendar")
                        scheduling_status = "Failed"
                        
                except Exception as schedule_error:
                    print(f"  ✗ Error scheduling interview: {str(schedule_error)}")
                    scheduling_status = "Error"
                    interview_date_str = "N/A"
                
                # Step 3.3: Update candidate status in Google Sheet
                print("  → Updating candidate status in sheet...")
                try:
                    update_result = automation_agent.update_candidate_in_sheet(
                        candidate_name=name,
                        candidate_email=email,
                        status=scheduling_status,
                        interview_date=interview_date_str,
                        spreadsheet_id=spreadsheet_id  # ALWAYS pass as argument
                    )

                    
                    # Step 3.4: Print success/fail for status update
                    if update_result:
                        print("  ✓ Candidate status updated in sheet successfully")
                    else:
                        print("  ⚠️  Failed to update candidate status in sheet")
                        
                except Exception as update_error:
                    print(f"  ✗ Error updating sheet: {str(update_error)}")
                    
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
