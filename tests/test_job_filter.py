import pytest
from unittest.mock import Mock
from job_filter import JobFilter

@pytest.fixture
def mock_config():
    config = Mock()
    config.blacklist_companies = ["bad company", "spam corp"]
    config.exclude_keywords = ["senior", "intern"]
    config.schedule_types = ["full-time"]
    config.trusted_domains = ["linkedin", "glassdoor", "indeed"]
    return config

def test_job_filter_valid_job(mock_config):
    """Test that a valid job passes the filter."""
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Software Engineer",
        "company_name": "Good Company",
        "apply_options": [{"title": "LinkedIn", "link": "https://linkedin.com/jobs/..."}]
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is True
    assert reason is None

def test_job_filter_blacklisted_company(mock_config):
    """Test that a job from a blacklisted company is rejected."""
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Software Engineer",
        "company_name": "Bad Company"
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is False
    assert reason is not None
    assert "Blacklisted company" in reason

def test_job_filter_blacklisted_company_case_insensitive(mock_config):
    """Test that company blacklist is case-insensitive."""
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Software Engineer",
        "company_name": "SPAM CORP"
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is False
    assert reason is not None
    assert "Blacklisted company" in reason

def test_job_filter_excluded_keyword(mock_config):
    """Test that a job with an excluded keyword in the title is rejected."""
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Senior Software Engineer",
        "company_name": "Good Company"
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is False
    assert reason is not None
    assert "Excluded keyword" in reason

def test_job_filter_excluded_keyword_case_insensitive(mock_config):
    """Test that keyword exclusion is case-insensitive."""
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Software Engineer Intern",
        "company_name": "Good Company"
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is False
    assert reason is not None
    assert "Excluded keyword" in reason

def test_job_filter_partial_keyword_match_should_not_reject(mock_config):
    """Test that partial keyword matches do NOT reject (e.g. 'lead' in 'leading')."""
    mock_config.exclude_keywords = ["lead"]
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Leading Tech Team",
        "company_name": "Good Company",
        "apply_options": [{"title": "LinkedIn", "link": "https://linkedin.com/jobs/..."}]
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is True
    assert reason is None

def test_job_filter_exact_word_match(mock_config):
    """Test that exact word matches are rejected."""
    mock_config.exclude_keywords = ["lead"]
    job_filter = JobFilter(mock_config)
    job = {
        "title": "Team Lead",
        "company_name": "Good Company"
    }
    is_valid, reason = job_filter.is_valid(job)
    assert is_valid is False
    assert reason is not None
    assert "Excluded keyword" in reason

def test_job_filter_punctuation_keyword(mock_config):
    """Test that keywords with punctuation (like 'sr.') are correctly filtered."""
    mock_config.exclude_keywords = ["sr."]
    job_filter = JobFilter(mock_config)
    
    # Should reject "Sr. Developer"
    job1 = {
        "title": "Sr. Developer",
        "company_name": "Good Company"
    }
    is_valid, reason = job_filter.is_valid(job1)
    assert is_valid is False
    assert "Excluded keyword" in reason # type: ignore

    # Should reject "Developer Sr."
    job2 = {
        "title": "Developer Sr.",
        "company_name": "Good Company"
    }
    is_valid, reason = job_filter.is_valid(job2)
    assert is_valid is False
    assert "Excluded keyword" in reason # type: ignore
    
    # Should NOT reject "Sr" (without dot) if only "sr." is excluded
    # (Though usually you'd exclude both, this tests exact matching)
    job3 = {
        "title": "Sr Developer",
        "company_name": "Good Company",
        "apply_options": [{"title": "LinkedIn", "link": "https://linkedin.com/jobs/..."}]
    }
    is_valid, reason = job_filter.is_valid(job3)
    assert is_valid is True

def test_filter_apply_options(mock_config):
    """Test filtering of apply options based on trusted domains and company website."""
    job_filter = JobFilter(mock_config)
    job = {
        "company_name": "Tech Corp",
        "apply_options": [
            {"title": "LinkedIn", "link": "https://linkedin.com/jobs/123"},
            {"title": "Glassdoor", "link": "https://glassdoor.com/job/456"},
            {"title": "Spam Board", "link": "https://spam-jobs.com/789"},
            {"title": "Tech Corp Careers", "link": "https://careers.techcorp.com/job/1"},
            {"title": "Random Site", "link": "https://random.com/job/2"}
        ]
    }
    
    filtered_options = job_filter.filter_apply_options(job)
    
    # Should keep LinkedIn, Glassdoor (trusted) and Tech Corp (direct company match)
    # Should remove Spam Board and Random Site
    assert len(filtered_options) == 3
    
    links = [opt['link'] for opt in filtered_options]
    assert "https://linkedin.com/jobs/123" in links
    assert "https://glassdoor.com/job/456" in links
    assert "https://careers.techcorp.com/job/1" in links
    assert "https://spam-jobs.com/789" not in links

def test_filter_apply_options_no_trusted_domains(mock_config):
    """Test that all options are returned if trusted_domains is None."""
    mock_config.trusted_domains = None
    job_filter = JobFilter(mock_config)
    job = {
        "company_name": "Tech Corp",
        "apply_options": [
            {"title": "Spam Board", "link": "https://spam-jobs.com/789"}
        ]
    }
    
    filtered_options = job_filter.filter_apply_options(job)
    assert len(filtered_options) == 1
    assert filtered_options[0]['link'] == "https://spam-jobs.com/789"
