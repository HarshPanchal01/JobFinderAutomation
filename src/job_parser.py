import logging
import base64
import json
import re
import urllib.parse
from salary_parser import SalaryParser
from date_parser import DateParser

class JobParser:
    @staticmethod
    def parse_job(job_data):
        """
        Extracts relevant fields from the raw job data.
        """
        title = job_data.get('title', 'N/A')
        logging.debug(f"Parsing job: {title}")
        company = job_data.get('company_name', 'N/A')
        location = job_data.get('location', 'N/A')
        
        # Enhanced Link Generation
        htidocid = JobParser._extract_htidocid(job_data)
        if htidocid:
            # Construct a clean desktop-friendly Google Jobs URL
            # We encode the htidocid to ensure safety in the URL
            safe_id = urllib.parse.quote(htidocid)
            link = f"https://www.google.com/search?ibp=htl;jobs#fpstate=tldetail&htivrt=jobs&htidocid={safe_id}"
        else:
            link = job_data.get('share_link')

        search_location = job_data.get('search_location', 'N/A')
        
        posted_date = "N/A"
        days_ago = None
        salary_info = None
        salary_raw = "N/A"
        
        if 'extensions' in job_data and job_data['extensions']:
            for item in job_data['extensions']:
                if 'ago' in item or 'day' in item:
                    posted_date = item
                    days_ago = DateParser.parse_days_ago(item)
                elif SalaryParser.is_salary_text(item):
                    salary_info = SalaryParser.parse_salary(item)
                    salary_raw = item
        
        # Also check detected_extensions if available (SerpApi specific)
        if not salary_info and 'detected_extensions' in job_data:
            exts = job_data['detected_extensions']
            if 'salary' in exts:
                salary_info = SalaryParser.parse_salary(exts['salary'])
                salary_raw = exts['salary']
            if 'posted_at' in exts and posted_date == "N/A":
                posted_date = exts['posted_at']
                days_ago = DateParser.parse_days_ago(posted_date)

        min_salary = salary_info[0] if salary_info else None
        max_salary = salary_info[1] if salary_info else None

        # Extract direct application options
        apply_options = job_data.get('apply_options', [])

        return {
            "title": title,
            "company": company,
            "location": location,
            "link": link,
            "posted_date": posted_date,
            "days_ago": days_ago,
            "search_location": search_location,
            "min_salary": min_salary,
            "max_salary": max_salary,
            "salary_raw": salary_raw,
            "apply_options": apply_options
        }

    @staticmethod
    def _extract_htidocid(job_data):
        """
        Reliably extracts the htidocid (Google's internal job ID) 
        from either the base64 encoded job_id or the share_link.
        """
        # Try 1: Decode job_id
        job_id = job_data.get('job_id')
        if job_id:
            try:
                # Add padding if needed for base64 decoding
                padded = job_id + '=' * (-len(job_id) % 4)
                decoded_bytes = base64.b64decode(padded)
                decoded_str = decoded_bytes.decode('utf-8')
                decoded_json = json.loads(decoded_str)
                
                if 'htidocid' in decoded_json:
                    return decoded_json['htidocid']
            except Exception:
                # Fail silently and try the next method
                pass
        
        # Try 2: Extract from share_link using regex
        share_link = job_data.get('share_link')
        if share_link:
            match = re.search(r'[?&]htidocid=([^&]+)', share_link)
            if match:
                raw_id = match.group(1)
                # Decode URL encoding (e.g. %3D -> =)
                return urllib.parse.unquote(raw_id)
        
        return None