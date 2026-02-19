import logging
import re
from urllib.parse import urlparse

class JobFilter:
    def __init__(self, config):
        self.blacklist_companies = [c.lower() for c in config.blacklist_companies]
        self.exclude_keywords = [k.lower() for k in config.exclude_keywords]
        self.schedule_types = [s.lower() for s in config.schedule_types]
        if getattr(config, "trusted_domains", None):
            self.trusted_domains = [d.lower() for d in config.trusted_domains]
        else:
            # None/empty means domain filtering disabled.
            self.trusted_domains = None

    def is_valid(self, job):
        """
        Checks if a job is valid based on blacklist, keywords, schedule type, and application sources.
        Returns (bool, reason).
        """
        title = job.get('title', '').lower()
        company = job.get('company_name', '').lower()
        schedule_type = job.get('detected_extensions', {}).get('schedule_type', '').lower()

        # Check company blacklist
        if company in self.blacklist_companies:
            return False, f"Blacklisted company: {job.get('company_name')}"
        
        # Check excluded keywords in title
        for keyword in self.exclude_keywords:
            # Use regex word boundary check to avoid partial matches (e.g. 'lead' in 'leading')
            # Handle special case where keyword ends with punctuation (like 'sr.')
            pattern = r''
            
            # Add leading boundary if keyword starts with a word char
            if keyword and keyword[0].isalnum():
                pattern += r'\b'
            
            pattern += re.escape(keyword)
            
            # Add trailing boundary if keyword ends with a word char
            if keyword and keyword[-1].isalnum():
                pattern += r'\b'
                
            if re.search(pattern, title):
                return False, f"Excluded keyword '{keyword}' in title: {job.get('title')}"

        # Check schedule type
        if schedule_type:
            # Check if any allowed schedule type is present in the job's schedule type string
            is_allowed = False
            for allowed_type in self.schedule_types:
                if allowed_type in schedule_type:
                    is_allowed = True
                    break
            
            if not is_allowed:
                return False, f"Invalid schedule type: {job.get('detected_extensions', {}).get('schedule_type')}"

        # Check application sources
        has_source, source_reason = self.has_reputable_source(job)
        if not has_source:
            return False, source_reason

        return True, None

    def filter_apply_options(self, job):
        """
        Filters the apply_options list to only include those from trusted domains
        or direct company sites.
        """
        apply_options = job.get('apply_options', [])
        if not apply_options:
            return []
            
        # If trusted domains is None (filtering disabled), return all options
        if not self.trusted_domains:
            return apply_options
            
        filtered_options = []
        company_name = job.get('company_name', '').lower()
        normalized_company = ''.join(e for e in company_name if e.isalnum())

        def _extract_hostname(raw_url: str) -> str:
            if not raw_url:
                return ""
            parsed = urlparse(raw_url)
            if not parsed.netloc and parsed.path and "://" not in raw_url:
                parsed = urlparse(f"https://{raw_url}")

            host = (parsed.hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            return host

        for option in apply_options:
            link = option.get('link', '').lower()
            title = option.get('title', '').lower()
            
            is_trusted = False
            # Check trusted domains
            for domain in self.trusted_domains:
                if domain in link or domain in title:
                    is_trusted = True
                    break
            
            # Check direct company page
            if not is_trusted:
                host = _extract_hostname(link)
                normalized_host = ''.join(c for c in host if c.isalnum())
                if normalized_company and normalized_company in normalized_host:
                    is_trusted = True
            
            if is_trusted:
                filtered_options.append(option)
                
        return filtered_options

    def has_reputable_source(self, job):
        """
        Checks if the job has at least one reputable application source.
        Returns (bool, reason).
        """
        apply_options = job.get('apply_options', [])
        if not apply_options:
            # If there are no apply options, we can't determine if it's reputable or not.
            # Assuming we want to filter these out as "low quality" or "not actionable".
            return False, "No application options found"

        # If domain filtering is disabled, allow all sources.
        if not self.trusted_domains:
            return True, None

        company_name = job.get('company_name', '').lower()
        # Normalize company name for URL check (remove spaces, punctuation could be tricky but let's start simple)
        normalized_company = ''.join(e for e in company_name if e.isalnum())

        def _extract_hostname(raw_url: str) -> str:
            """Best-effort hostname extraction, tolerant of missing scheme."""
            if not raw_url:
                return ""
            parsed = urlparse(raw_url)
            if not parsed.netloc and parsed.path and "://" not in raw_url:
                parsed = urlparse(f"https://{raw_url}")

            host = (parsed.hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            return host
        
        for option in apply_options:
            link = option.get('link', '').lower()
            title = option.get('title', '').lower()
            
            # Check trusted domains
            for domain in self.trusted_domains:
                if domain in link or domain in title:
                    return True, None
            
            # Check direct company page
            # Heuristic: company name must appear in the hostname (not just the path)
            # This avoids aggregators like job boards embedding the company name in a URL slug.
            host = _extract_hostname(link)
            normalized_host = ''.join(c for c in host if c.isalnum())
            if normalized_company and normalized_company in normalized_host:
                return True, None
                    
        return False, "No reputable application source found"
