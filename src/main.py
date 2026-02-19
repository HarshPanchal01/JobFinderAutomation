import logging
import os
import shutil
from datetime import datetime
from config import Config
from job_finder import JobFinder
from file_manager import FileManager
from job_history import JobHistory
from job_parser import JobParser
from job_filter import JobFilter
from email_notification import EmailNotification
from utils import format_location_for_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starting Job Finder Automation...")
    # Initialize configuration
    config = Config()
    logging.info("Configuration loaded.")
    
    if not config.api_key:
        logging.error("API_KEY not found in environment variables.")
        return

    # Initialize JobFinder and JobHistory
    finder = JobFinder(config.api_key, max_pages=config.max_pages)
    history = JobHistory()
    job_filter = JobFilter(config)
    logging.info(f"JobFinder initialized with max_pages={config.max_pages}.")
    
    all_jobs = []
    
    for query in config.queries:
        for location in config.locations:
            logging.info(f"Searching for '{query}' in {location}...")
            # Execute search
            search_params = config.search_params.copy()
            
            # Format location for query (e.g. "Toronto, ON")
            short_location = format_location_for_query(location)
            
            # Update query to include "near location" for better results
            search_params["q"] = f"{query} near {short_location}"
            search_params["location"] = location
            
            jobs = finder.search_jobs(search_params)
            logging.info(f"Found {len(jobs)} jobs for '{query}' in {location} (using '{short_location}').")
            all_jobs.extend(jobs)
    
    # Deduplicate aggregated results (intra-run duplicates)
    all_jobs = finder.removeDuplicates(all_jobs)
    logging.info(f"Total unique jobs found in this run: {len(all_jobs)}")

    # Filter out jobs seen in previous runs (inter-run duplicates)
    # AND filter by salary if configured
    # AND filter by date if configured
    # AND filter by blacklist/keywords
    new_jobs = []
    skipped_salary = 0
    skipped_date = 0
    skipped_history = 0
    skipped_filter = 0
    
    for job in all_jobs:
        # Check history first
        if history.is_seen(job):
            skipped_history += 1
            continue
            
        # Check blacklist and keywords
        is_valid, reason = job_filter.is_valid(job)
        if not is_valid:
            logging.info(f"Skipping job: {reason}")
            skipped_filter += 1
            continue

        parsed_job = JobParser.parse_job(job)
        salary_str = parsed_job.get('salary_raw', 'N/A')
        days_ago = parsed_job.get('days_ago')

        # Check date if max_days_old is set
        if days_ago is not None and days_ago > config.max_days_old:
            logging.info(f"Skipping job: {parsed_job['title']} - Posted: {parsed_job['posted_date']} (Older than {config.max_days_old} days)")
            skipped_date += 1
            continue

        # Check salary if min_salary is set
        if config.min_salary > 0:
            max_salary = parsed_job.get('max_salary')
            
            # If salary is known AND strictly less than min_salary, skip it
            if max_salary and max_salary < config.min_salary:
                logging.info(f"Skipping job: {parsed_job['title']} - Salary: {salary_str} (Below {config.min_salary})")
                skipped_salary += 1
                continue
        
        # Filter apply options to only include trusted domains
        job['apply_options'] = job_filter.filter_apply_options(job)
        
        logging.info(f"Found job: {parsed_job['title']} - Salary: {salary_str} - Posted: {parsed_job['posted_date']}")
        new_jobs.append(job)
        history.add_job(job)
    
    logging.info(f"Skipped {skipped_history} jobs due to history (already seen).")
    logging.info(f"Skipped {skipped_filter} jobs due to filters (blacklist/keywords/schedule/sources).")
    logging.info(f"Skipped {skipped_salary} jobs due to low salary.")
    logging.info(f"Skipped {skipped_date} jobs due to age.")
    logging.info(f"Net new jobs after history, salary, and date check: {len(new_jobs)}")
    
    # Save results
    logging.info("Saving results...")
    FileManager.save_json(new_jobs, 'jobs.json')
    FileManager.save_markdown(new_jobs, 'jobs.md')
    
    # Check if jobs.md is too large for GitHub Issue body (limit is ~65536 chars)
    # We use a safe limit of 60000 to account for overhead
    if os.path.getsize('jobs.md') < 60000:
        logging.info("Report is small enough for GitHub Issue. Copying to summary.md.")
        shutil.copy('jobs.md', 'summary.md')
    else:
        logging.info("Report is too large. Generating condensed summary.")
        FileManager.save_summary_markdown(new_jobs, 'summary.md')
    
    # Save history and cleanup
    history.save_history()
    history.cleanup_old_entries()
    
    logging.info(f"Total SerpApi calls made in this session: {finder.total_api_calls}")

    # Send Email Notification
    if config.email_address and config.email_password:
        logging.info("Email configuration found. Sending notification...")
        email_notifier = EmailNotification(
            config.smtp_server,
            config.smtp_port,
            config.email_address,
            config.email_password
        )
        
        report_date = datetime.now().strftime("%Y-%m-%d")
        subject = f"Weekly Jobs Report - {report_date}"

        github_issues_url = "https://github.com/HarshPanchal01/Job-Finder-Automation/issues?q=is%3Aissue%20state%3Aclosed"
        
        # Use jobs.md for the email body as it contains the full report
        email_notifier.send_email(
            config.email_receivers,
            subject,
            "jobs.md",
            github_issue_url=github_issues_url,
        )
    else:
        logging.info("Email configuration not found. Skipping email notification.")

    logging.info("Automation completed successfully.")

if __name__ == "__main__":
    main()