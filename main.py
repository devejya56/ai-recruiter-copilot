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

import sys
import traceback
from typing import List, Dict, Any
from datetime import datetime, timedelta
from agents.automation_agent import AutomationAgent


def print_banner(text: str, emoji: str = "🚀"):
    """Print a styled banner for major sections."""
    width = 60
    print("\n" + "=" * width)
    print(f"{emoji}  {text.center(width - 4)}  {emoji}")
    print("=" * width)


def print_section(text: str, emoji: str = "📋"):
    """Print a section header."""
    print(f"\n{emoji} {text}")
    print("-" * 50)


def print_candidate_status(candidate_num: int, name: str, email: str, status: str, interview_date: str = "N/A"):
    """Print a compact one-block summary for a candidate."""
    status_emoji = {
        "Scheduled": "✅",
        "Failed": "❌",
        "Error": "⚠️"
    }.get(status, "❓")
    
    print(f"\n  {status_emoji} Candidate {candidate_num}: {name}")
    print(f"     Email: {email}")
    print(f"     Status: {status} | Interview: {interview_date}")


def print_summary(total: int, successful: int, failed: int):
    """Print final summary statistics."""
    print("\n" + "=" * 60)
    print(f"📊 Summary: {successful}/{total} successful, {failed} failed")
    print("=" * 60 + "\n")


def main():
    """
    Main orchestration function that runs the complete recruitment workflow.
    """
    print_banner("AI Recruiter Copilot", "🤖")
    
    successful_count = 0
    failed_count = 0
    
    try:
        # Step 1: Initialize AutomationAgent
        print_section("Initializing AutomationAgent", "⚙️")
        automation_agent = AutomationAgent()
        print("✓ Ready")
        
        # Step 2: Parse candidates from Gmail resumes
        print_section("Parsing Gmail Resumes", "📧")
        candidates = automation_agent.parse_gmail_resumes()
        
        if not candidates:
            print("⚠️  No candidates found")
            return
        
        print(f"✓ Found {len(candidates)} candidate(s)")
        
        # Step 3: For each candidate, schedule interview and update status
        print_section("Processing Candidates", "👥")
        
        for i, candidate in enumerate(candidates, 1):
            try:
                # Use attribute access, not dict access
                name = getattr(candidate, 'name', f'Candidate {i}')
                email = getattr(candidate, 'email', '')
                
                scheduling_status = "Failed"
                interview_date_str = "N/A"
                
                # Step 3.1: Schedule interview in calendar
                try:
                    # Calculate interview date (7 days from now at 10 AM)
                    interview_date = datetime.now() + timedelta(days=7)
                    interview_date = interview_date.replace(hour=10, minute=0, second=0, microsecond=0)
                    interview_date_str = interview_date.strftime("%Y-%m-%d %H:%M")
                    
                    schedule_result = automation_agent.schedule_interview_in_calendar(
                        candidate_name=name,
                        candidate_email=email,
                        interview_date=interview_date
                    )
                    
                    if schedule_result:
                        scheduling_status = "Scheduled"
                        successful_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as schedule_error:
                    print(f"  ✗ Error scheduling interview for {name}: {str(schedule_error)}")
                    scheduling_status = "Error"
                    interview_date_str = "N/A"
                    failed_count += 1
                
                # Step 3.2: Update candidate status in Google Sheet
                try:
                    automation_agent.update_candidate_in_sheet(
                        candidate_name=name,
                        candidate_email=email,
                        status=scheduling_status,
                        interview_date=interview_date_str,
                        spreadsheet_id=spreadsheet_id
                    )
                except Exception as update_error:
                    print(f"  ✗ Error updating sheet for {name}: {str(update_error)}")
                
                # Print compact candidate status
                print_candidate_status(i, name, email, scheduling_status, interview_date_str)
                    
            except Exception as e:
                # Use attribute access for error messages too
                name = getattr(candidate, 'name', f'Candidate {i}')
                email = getattr(candidate, 'email', '')
                
                print(f"  ✗ Error processing candidate {name} ({email}): {str(e)}")
                traceback.print_exc()
                failed_count += 1
                continue
        
        # Print summary
        print_summary(len(candidates), successful_count, failed_count)
        print_banner("Copilot Finished", "🎉")
        
    except Exception as e:
        print(f"\n✗ Fatal error in main workflow: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
