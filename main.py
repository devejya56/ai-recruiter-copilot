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
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.get('name', 'Unknown')} - {candidate.get('email', 'No email')}")
        
        # Step 3: Process each candidate
        print("\n[Step 3] Processing candidates...")
        results = {
            'successful_interviews': [],
            'failed_interviews': [],
            'successful_updates': [],
            'failed_updates': []
        }
        
        for i, candidate in enumerate(candidates, 1):
            candidate_name = candidate.get('name', f'Candidate {i}')
            candidate_email = candidate.get('email', '')
            
            print(f"\n--- Processing {candidate_name} ({i}/{len(candidates)}) ---")
            
            # Step 3a: Schedule interview in calendar
            try:
                print(f"  Scheduling interview for {candidate_name}...")
                interview_result = automation_agent.schedule_interview_in_calendar(
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    candidate_data=candidate
                )
                
                if interview_result and interview_result.get('success', False):
                    print(f"  ✓ Interview scheduled successfully")
                    results['successful_interviews'].append({
                        'candidate': candidate_name,
                        'result': interview_result
                    })
                else:
                    print(f"  ✗ Failed to schedule interview")
                    results['failed_interviews'].append({
                        'candidate': candidate_name,
                        'error': interview_result.get('error', 'Unknown error')
                    })
            
            except Exception as e:
                print(f"  ✗ Exception during interview scheduling: {str(e)}")
                results['failed_interviews'].append({
                    'candidate': candidate_name,
                    'error': str(e)
                })
            
            # Step 3b: Update candidate status in Sheets
            try:
                print(f"  Updating candidate status in Sheets...")
                
                # Determine status based on interview scheduling result
                status = "Interview Scheduled" if candidate_name in [r['candidate'] for r in results['successful_interviews']] else "Interview Pending"
                
                sheet_result = automation_agent.update_candidate_in_sheet(
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    status=status,
                    candidate_data=candidate
                )
                
                if sheet_result and sheet_result.get('success', False):
                    print(f"  ✓ Candidate status updated successfully")
                    results['successful_updates'].append({
                        'candidate': candidate_name,
                        'status': status,
                        'result': sheet_result
                    })
                else:
                    print(f"  ✗ Failed to update candidate status")
                    results['failed_updates'].append({
                        'candidate': candidate_name,
                        'error': sheet_result.get('error', 'Unknown error')
                    })
            
            except Exception as e:
                print(f"  ✗ Exception during status update: {str(e)}")
                results['failed_updates'].append({
                    'candidate': candidate_name,
                    'error': str(e)
                })
        
        # Step 4: Print final results
        print("\n=== FINAL RESULTS ===")
        
        print(f"\n📅 INTERVIEW SCHEDULING:")
        print(f"  ✓ Successful: {len(results['successful_interviews'])}")
        for result in results['successful_interviews']:
            print(f"    - {result['candidate']}")
        
        print(f"  ✗ Failed: {len(results['failed_interviews'])}")
        for result in results['failed_interviews']:
            print(f"    - {result['candidate']}: {result['error']}")
        
        print(f"\n📊 STATUS UPDATES:")
        print(f"  ✓ Successful: {len(results['successful_updates'])}")
        for result in results['successful_updates']:
            print(f"    - {result['candidate']}: {result['status']}")
        
        print(f"  ✗ Failed: {len(results['failed_updates'])}")
        for result in results['failed_updates']:
            print(f"    - {result['candidate']}: {result['error']}")
        
        # Summary
        total_candidates = len(candidates)
        successful_complete = len([c for c in results['successful_interviews'] 
                                 if c['candidate'] in [u['candidate'] for u in results['successful_updates']]])
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total candidates processed: {total_candidates}")
        print(f"  Fully processed (interview + status): {successful_complete}")
        print(f"  Success rate: {(successful_complete/total_candidates)*100:.1f}%")
        
        print("\n=== AI Recruiter Copilot Completed ===")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
