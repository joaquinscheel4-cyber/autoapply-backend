"""
Base connector interface. Every source implements this.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class NormalizedJob:
    """Standard job format across all sources."""
    external_id: str          # source_prefix + original_id
    source: str               # 'computrabajo' | 'greenhouse' | 'lever' | ...
    title: str
    company: str
    location: str
    country: str = "CL"
    modality: Optional[str] = None    # 'remote' | 'hybrid' | 'presencial'
    employment_type: Optional[str] = None  # 'full-time' | 'part-time' | 'contract'
    description: str = ""
    apply_link: Optional[str] = None
    apply_email: Optional[str] = None
    skills: list = field(default_factory=list)
    seniority: Optional[str] = None   # 'junior' | 'semi-senior' | 'senior' | 'lead'
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "CLP"
    posted_at: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "external_id": self.external_id,
            "source": self.source,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "country": self.country,
            "modality": self.modality,
            "description": self.description,
            "apply_link": self.apply_link,
            "apply_email": self.apply_email,
            "skills": self.skills,
            "seniority": self.seniority,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "posted_at": self.posted_at,
            "fetched_at": self.fetched_at,
        }


class BaseConnector(ABC):
    """Abstract base for all job source connectors."""

    name: str = "base"
    rate_limit_seconds: float = 0.5  # Delay between requests

    @abstractmethod
    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        """Fetch and return normalized jobs for the given roles."""
        pass

    def log(self, msg: str):
        print(f"[{self.name.upper()}] {msg}")
