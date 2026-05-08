from __future__ import annotations

from decimal import Decimal
from math import ceil

from app.models.stadium import Stadium
from app.models.team import Team

BASE_TICKET_PRICE = Decimal("20.00")
TICKET_PRICE_QUANT = Decimal("0.01")
TOP_THIRD_COEFFICIENT = Decimal("2.0")
MIDDLE_THIRD_COEFFICIENT = Decimal("1.5")
BOTTOM_THIRD_COEFFICIENT = Decimal("1.1")


class TicketPriceService:
    def calculate_default_price(
        self,
        *,
        stadium: Stadium,
        home_team: Team,
        away_team: Team,
        previous_season_table_size: int | None,
    ) -> Decimal:
        """Calculate default ticket price from stadium capacity and team places."""
        capacity_factor = self.get_capacity_factor(stadium.capacity)
        club_coefficient = max(
            self.get_club_coefficient(
                home_team.previous_season_place,
                previous_season_table_size,
            ),
            self.get_club_coefficient(
                away_team.previous_season_place,
                previous_season_table_size,
            ),
        )
        return ((BASE_TICKET_PRICE + capacity_factor) * club_coefficient).quantize(
            TICKET_PRICE_QUANT
        )

    def get_capacity_factor(self, capacity: int) -> Decimal:
        if capacity >= 60_000:
            return Decimal("15.00")
        if capacity >= 30_000:
            return Decimal("10.00")
        if capacity >= 10_000:
            return Decimal("5.00")
        return Decimal("0.00")

    def get_club_coefficient(
        self,
        previous_season_place: int | None,
        previous_season_table_size: int | None,
    ) -> Decimal:
        if previous_season_place is None or previous_season_table_size is None:
            return BOTTOM_THIRD_COEFFICIENT
        if previous_season_table_size <= 0:
            return BOTTOM_THIRD_COEFFICIENT

        top_limit = ceil(previous_season_table_size / 3)
        middle_limit = ceil(previous_season_table_size * 2 / 3)
        if previous_season_place <= top_limit:
            return TOP_THIRD_COEFFICIENT
        if previous_season_place <= middle_limit:
            return MIDDLE_THIRD_COEFFICIENT
        return BOTTOM_THIRD_COEFFICIENT
