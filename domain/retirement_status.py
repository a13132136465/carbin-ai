from enum import Enum


class RetirementStatus(str, Enum):

    PENDING = "PENDING"

    CONFIRMED = "CONFIRMED"

    FAILED = "FAILED"
