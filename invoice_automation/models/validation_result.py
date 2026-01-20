"""
Validation Result data models for tracking invoice validation outcomes.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any

from .invoice import Invoice
from .po_record import PORecord


class ValidationSeverity(Enum):
    """Severity levels for validation checks."""
    ERROR = "ERROR"      # Critical error, blocks auto-update
    WARNING = "WARNING"  # Non-critical issue, flag for review
    INFO = "INFO"        # Informational message


@dataclass
class Validation:
    """
    Represents a single validation check result.

    Attributes:
        check_name: Name/description of the validation check
        passed: Whether the validation passed
        expected: Expected value
        actual: Actual value found
        severity: Severity level (ERROR, WARNING, INFO)
        message: Detailed message explaining the result
    """
    check_name: str
    passed: bool
    expected: Any
    actual: Any
    severity: ValidationSeverity
    message: str

    def __repr__(self) -> str:
        status = "✓" if self.passed else "✗"
        return f"{status} {self.check_name}: {self.message}"


@dataclass
class ValidationResult:
    """
    Represents the complete validation result for an invoice.

    Attributes:
        invoice: The invoice being validated
        po_record: The matched PO record (if found)
        validations: List of individual validation checks
        is_valid: Overall validation status
        can_auto_update: Whether invoice can be auto-updated
        errors: List of error messages
        warnings: List of warning messages
        pdf_path: Path to the source PDF file
    """
    invoice: Optional[Invoice]
    po_record: Optional[PORecord]
    validations: List[Validation] = field(default_factory=list)
    is_valid: bool = False
    can_auto_update: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    pdf_path: str = ""

    def add_validation(self, validation: Validation) -> None:
        """Add a validation check result."""
        self.validations.append(validation)

        if not validation.passed:
            if validation.severity == ValidationSeverity.ERROR:
                self.errors.append(validation.message)
            elif validation.severity == ValidationSeverity.WARNING:
                self.warnings.append(validation.message)

    def finalize(self) -> None:
        """
        Finalize validation result by determining overall status.
        Sets is_valid and can_auto_update based on validation results.
        """
        has_errors = any(
            not v.passed and v.severity == ValidationSeverity.ERROR
            for v in self.validations
        )

        self.is_valid = not has_errors
        self.can_auto_update = self.is_valid and self.po_record is not None

    def get_status_summary(self) -> str:
        """Get a summary status string."""
        if self.can_auto_update:
            return "SUCCESS"
        elif self.errors:
            return "ERROR"
        elif self.warnings:
            return "WARNING"
        else:
            return "UNKNOWN"

    @classmethod
    def create_error(cls, pdf_path: str, error_message: str, invoice: Optional[Invoice] = None):
        """Create a validation result representing a critical error."""
        result = cls(
            invoice=invoice,
            po_record=None,
            pdf_path=pdf_path,
            is_valid=False,
            can_auto_update=False,
            errors=[error_message]
        )
        result.add_validation(Validation(
            check_name="Critical Error",
            passed=False,
            expected=None,
            actual=None,
            severity=ValidationSeverity.ERROR,
            message=error_message
        ))
        return result

    def __repr__(self) -> str:
        invoice_num = self.invoice.invoice_number if self.invoice else "N/A"
        return (
            f"ValidationResult(invoice_number='{invoice_num}', "
            f"status='{self.get_status_summary()}', "
            f"errors={len(self.errors)}, warnings={len(self.warnings)})"
        )
