"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.admin import Admin
from app.models.hours_application import HoursApplication
from app.models.opportunity_application import OpportunityApplication
from app.models.student import Student
from app.models.volunteer_opportunity import VolunteerOpportunity

__all__ = [
	"Admin",
	"HoursApplication",
	"OpportunityApplication",
	"Student",
	"User",
	"VolunteerOpportunity",
]
