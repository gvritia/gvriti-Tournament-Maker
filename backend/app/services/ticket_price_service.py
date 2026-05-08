from decimal import Decimal

from app.models.stadium import Stadium
from app.models.team import Team


class TicketPriceService:
    def calculate_default_price(
        self,
        *,
        stadium: Stadium,
        home_team: Team,
        away_team: Team,
    ) -> Decimal:
        """Calculate default ticket price from stadium capacity and team places."""
        raise NotImplementedError(
            "Ticket pricing will be implemented after CRUD setup."
        )
