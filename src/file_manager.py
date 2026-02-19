import json
import logging
from job_parser import JobParser

class FileManager:
    @staticmethod
    def save_json(data, filename):
        """
        Saves the raw data to a JSON file.
        """
        logging.info(f"Saving JSON data to {filename}...")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Job results saved to {filename}")

    @staticmethod
    def save_summary_markdown(jobs, filename):
        """
        Saves a summary of the job data to a Markdown file.
        Used for the GitHub Issue body to avoid character limits.
        """
        logging.info(f"Saving Summary Markdown data to {filename}...")
        
        # Group jobs by search_location
        jobs_by_location = {}
        for job in jobs:
            parsed_job = JobParser.parse_job(job)
            # Use 'Unknown Location' if search_location is missing
            loc = parsed_job.get('search_location', 'Unknown Location')
            if loc not in jobs_by_location:
                jobs_by_location[loc] = []
            jobs_by_location[loc].append(parsed_job)
            
        with open(filename, 'w', encoding="utf-8") as f:
            f.write("# Weekly Job Search Results (Summary)\n\n")
            
            if not jobs:
                f.write("No jobs found this week.\n")
                logging.info(f"Job results summary saved to {filename}")
                return

            # Summary Section
            f.write("## Summary\n\n")
            f.write(f"**Total Jobs Found:** {len(jobs)}\n\n")
            f.write("| Location | Jobs |\n")
            f.write("| :--- | :---: |\n")
            for location in sorted(jobs_by_location.keys()):
                count = len(jobs_by_location[location])
                f.write(f"| {location} | {count} |\n")
            f.write("\n---\n\n")
            f.write("**Note:** The full report is too long to display here. Please download the `job-reports` artifact from the Workflow Run to see all job details.\n")
        
        logging.info(f"Job results summary saved to {filename}")

    @staticmethod
    def save_markdown(jobs, filename):
        """
        Saves the parsed job data to a Markdown file, grouped by search location.
        Includes a summary table and collapsible sections.
        """
        logging.info(f"Saving Markdown data to {filename}...")
        
        # Group jobs by search_location
        jobs_by_location = {}
        for job in jobs:
            parsed_job = JobParser.parse_job(job)
            # Use 'Unknown Location' if search_location is missing
            loc = parsed_job.get('search_location', 'Unknown Location')
            if loc not in jobs_by_location:
                jobs_by_location[loc] = []
            jobs_by_location[loc].append(parsed_job)
            
        with open(filename, 'w', encoding="utf-8") as f:
            f.write("# Weekly Job Search Results\n\n")
            
            if not jobs:
                f.write("No jobs found this week.\n")
                logging.info(f"Job results summary saved to {filename}")
                return

            # Summary Section
            f.write("## Summary\n\n")
            f.write(f"**Total Jobs Found:** {len(jobs)}\n\n")
            f.write("| Location | Jobs |\n")
            f.write("| :--- | :---: |\n")
            for location in sorted(jobs_by_location.keys()):
                count = len(jobs_by_location[location])
                f.write(f"| {location} | {count} |\n")
            f.write("\n---\n\n")

            # Detailed Listings
            for location in sorted(jobs_by_location.keys()):
                count = len(jobs_by_location[location])
                f.write(f"### {location} ({count})\n\n")
                
                # Collapsible section
                f.write("<details>\n")
                f.write(f"<summary>Click to view {count} jobs in {location}</summary>\n\n")
                
                for job in jobs_by_location[location]:
                    title = job['title']
                    company = job['company']
                    job_location = job['location']
                    posted_date = job['posted_date']
                    link = job['link']
                    salary = job.get('salary_raw', 'N/A')

                    f.write(f"#### {title}\n")
                    f.write(f"- **Company:** {company}\n")
                    f.write(f"- **Location:** {job_location}\n")
                    f.write(f"- **Posted:** {posted_date}\n")
                    if salary != 'N/A':
                        f.write(f"- **Salary:** **{salary}**\n")
                    else:
                        f.write(f"- **Salary:** {salary}\n")
                    
                    if link:
                        f.write(f"- [**View on Google Jobs**]({link})\n")
                    
                    apply_options = job.get('apply_options', [])
                    if apply_options:
                        f.write("- **Apply Directly:**\n")
                        for option in apply_options:
                            opt_title = option.get('title', 'Apply')
                            opt_link = option.get('link', '#')
                            f.write(f"  - [{opt_title}]({opt_link})\n")
                    
                    f.write("\n---\n\n")
                
                f.write("</details>\n\n")
        
        logging.info(f"Job results summary saved to {filename}")