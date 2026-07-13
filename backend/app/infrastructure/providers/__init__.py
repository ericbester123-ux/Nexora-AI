from app.infrastructure.providers.base import BaseOpportunityProvider, NormalizedOpportunity
from app.infrastructure.providers.freelancer_mock import MockFreelancerProvider
from app.infrastructure.providers.freelancer_real import FreelancerProvider
from app.infrastructure.providers.registry import ProviderRegistry

__all__ = ["BaseOpportunityProvider", "NormalizedOpportunity", "MockFreelancerProvider", "FreelancerProvider", "ProviderRegistry"]
