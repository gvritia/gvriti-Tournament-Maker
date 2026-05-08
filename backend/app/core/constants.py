from enum import StrEnum


class UserRole(StrEnum):
    ORGANIZER = "organizer"
    ADMIN = "admin"


class SeasonStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    FINISHED = "finished"
    ARCHIVED = "archived"


class TournamentType(StrEnum):
    CHAMPIONSHIP = "championship"
    CUP = "cup"


class TournamentStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class MatchStatus(StrEnum):
    SCHEDULED = "scheduled"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class CupStage(StrEnum):
    SEMIFINAL = "semifinal"
    FINAL = "final"


class MatchEventType(StrEnum):
    GOAL = "goal"
    ASSIST = "assist"
    SAVE = "save"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"


class PlayerPosition(StrEnum):
    GOALKEEPER = "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"
