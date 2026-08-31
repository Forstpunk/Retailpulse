from dataclasses import dataclass
from enum import StrEnum


class QualityStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class QualityCheckType(StrEnum):
    """
    What kind of thing a quality check verifies. Drives
    how operators triage a failure: a COMPLETENESS miss
    means data didn't arrive; a FINANCIAL_CONSISTENCY miss
    means data arrived but is wrong.
    """

    COMPLETENESS = "COMPLETENESS"
    UNIQUENESS = "UNIQUENESS"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    FINANCIAL_CONSISTENCY = "FINANCIAL_CONSISTENCY"


class QualitySeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class QualityCheckResult:
    check_name: str
    status: QualityStatus
    observed_value: int | float | str
    expected_value: int | float | str | None
    message: str
    check_type: QualityCheckType
    severity: QualitySeverity = (
        QualitySeverity.ERROR
    )


@dataclass(frozen=True)
class QualityReport:
    checks: tuple[QualityCheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(
            check.status == QualityStatus.PASS
            for check in self.checks
        )

    @property
    def failed_checks(
        self,
    ) -> tuple[QualityCheckResult, ...]:
        return tuple(
            check
            for check in self.checks
            if check.status == QualityStatus.FAIL
        )