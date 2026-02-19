import logging
from job_parser import JobParser

def test_parse_job_full_data():
    """Test parsing a job with all fields present."""
    logging.info("Testing parse_job with full data...")
    raw_job = {
        "title": "Software Engineer",
        "company_name": "Tech Corp",
        "location": "Remote",
        "share_link": "http://example.com/job",
        "search_location": "Global",
        "extensions": ["2 days ago", "Full-time"]
    }
    
    parsed = JobParser.parse_job(raw_job)
    
    assert parsed["title"] == "Software Engineer"
    assert parsed["company"] == "Tech Corp"
    assert parsed["location"] == "Remote"
    assert parsed["link"] == "http://example.com/job"
    assert parsed["search_location"] == "Global"
    assert parsed["posted_date"] == "2 days ago"
    logging.info("parse_job full data test passed.")

def test_parse_job_missing_fields():
    """Test parsing a job with missing fields."""
    logging.info("Testing parse_job with missing fields...")
    raw_job = {}
    
    parsed = JobParser.parse_job(raw_job)
    
    assert parsed["title"] == "N/A"
    assert parsed["company"] == "N/A"
    assert parsed["location"] == "N/A"
    assert parsed["link"] is None
    assert parsed["search_location"] == "N/A"
    assert parsed["posted_date"] == "N/A"
    logging.info("parse_job missing fields test passed.")

def test_parse_job_posted_date_extraction():
    """Test extraction of posted date from extensions."""
    logging.info("Testing parse_job posted date extraction...")
    raw_job = {
        "extensions": ["Full-time", "3 days ago", "Apply on site"]
    }
    
    parsed = JobParser.parse_job(raw_job)
    assert parsed["posted_date"] == "3 days ago"
    assert parsed["days_ago"] == 3
    logging.info("parse_job posted date extraction test passed.")

def test_parse_job_salary_extraction():
    """Test extraction of salary from extensions."""
    logging.info("Testing parse_job salary extraction...")
    raw_job = {
        "extensions": ["Full-time", "$100k - $120k a year"]
    }
    
    parsed = JobParser.parse_job(raw_job)
    assert parsed["min_salary"] == 100000
    assert parsed["max_salary"] == 120000
    assert parsed["salary_raw"] == "$100k - $120k a year"
    logging.info("parse_job salary extraction test passed.")

def test_parse_job_detected_extensions_salary():
    """Test extraction of salary from detected_extensions."""
    logging.info("Testing parse_job detected_extensions salary...")
    raw_job = {
        "detected_extensions": {"salary": "$50/hr"}
    }
    
    parsed = JobParser.parse_job(raw_job)
    assert parsed["min_salary"] == 104000
    assert parsed["max_salary"] == 104000
    logging.info("parse_job detected_extensions salary test passed.")

def test_parse_job_with_htidocid():
    """Test parsing a job with a valid job_id containing htidocid."""
    logging.info("Testing parse_job with htidocid...")
    # Base64 encoded JSON: {"htidocid": "test_id_123"}
    # echo -n '{"htidocid": "test_id_123"}' | base64
    # eyJodGlkb2NpZCI6ICJ0ZXN0X2lkXzEyMyJ9
    
    raw_job = {
        "title": "Software Engineer",
        "company_name": "Tech Corp",
        "job_id": "eyJodGlkb2NpZCI6ICJ0ZXN0X2lkXzEyMyJ9",
        "share_link": "http://old-link.com"
    }
    
    parsed = JobParser.parse_job(raw_job)
    
    expected_link = "https://www.google.com/search?ibp=htl;jobs#fpstate=tldetail&htivrt=jobs&htidocid=test_id_123"
    assert parsed["link"] == expected_link
    logging.info("parse_job htidocid test passed.")
