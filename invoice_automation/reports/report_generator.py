"""
Report generator for invoice processing results.
"""
from pathlib import Path
from typing import List
from datetime import datetime

from ..models import ValidationResult


class ReportGenerator:
    """Generator for processing reports."""

    def __init__(self, results: List[ValidationResult]):
        """
        Initialize report generator.

        Args:
            results: List of validation results
        """
        self.results = results

    def generate_summary(self) -> str:
        """
        Generate a summary report.

        Returns:
            Summary text
        """
        total = len(self.results)
        auto_updated = sum(1 for r in self.results if r.can_auto_update)
        flagged = sum(1 for r in self.results if not r.can_auto_update and r.is_valid)
        failed = sum(1 for r in self.results if not r.is_valid)

        summary = [
            "",
            "=" * 60,
            "Invoice Processing Summary",
            "=" * 60,
            f"Total Invoices Processed: {total}",
            f"Auto-Updated Successfully: {auto_updated}",
            f"Flagged for Manual Review: {flagged}",
            f"Failed to Process: {failed}",
            "=" * 60,
            ""
        ]

        # List invoices by status
        if auto_updated > 0:
            summary.append("\nAuto-Updated Invoices:")
            for result in self.results:
                if result.can_auto_update:
                    inv_num = result.invoice.invoice_number if result.invoice else "N/A"
                    amount = f"£{result.invoice.net_amount:.2f}" if result.invoice else "N/A"
                    supplier = result.invoice.supplier_name if result.invoice else "N/A"
                    summary.append(f"  ✓ {inv_num} - {supplier} - {amount}")

        if flagged > 0 or failed > 0:
            summary.append("\nRequires Manual Review:")
            for result in self.results:
                if not result.can_auto_update:
                    inv_num = result.invoice.invoice_number if result.invoice else "N/A"
                    supplier = result.invoice.supplier_name if result.invoice else "Unknown"
                    errors = ", ".join(result.errors[:2])  # First 2 errors
                    summary.append(f"  ✗ {inv_num} - {supplier} - {errors}")

        return "\n".join(summary)

    def save_summary_csv(self, output_path: Path):
        """
        Save summary report as CSV.

        Args:
            output_path: Path to save CSV file
        """
        import csv

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Status', 'Invoice Number', 'Supplier', 'PO Number', 'Store', 'Amount', 'Validations', 'Errors'])

            for result in self.results:
                if result.invoice:
                    status = result.get_status_summary()
                    inv_num = result.invoice.invoice_number
                    supplier = result.invoice.supplier_name
                    po_num = result.invoice.po_number
                    store = result.invoice.store_location
                    amount = f"£{result.invoice.net_amount:.2f}"
                    validations = f"{sum(1 for v in result.validations if v.passed)}/{len(result.validations)} passed"
                    errors = "; ".join(result.errors)

                    writer.writerow([status, inv_num, supplier, po_num, store, amount, validations, errors])

    def save_detailed_report(self, output_path: Path):
        """
        Save detailed validation report.

        Args:
            output_path: Path to save report file
        """
        lines = []
        lines.append(f"Invoice Processing Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        for i, result in enumerate(self.results, 1):
            lines.append(f"\n{i}. Invoice: {result.invoice.invoice_number if result.invoice else 'N/A'}")
            lines.append("-" * 80)

            if result.invoice:
                lines.append(f"   Supplier: {result.invoice.supplier_name}")
                lines.append(f"   PO Number: {result.invoice.po_number}")
                lines.append(f"   Store: {result.invoice.store_location}")
                lines.append(f"   Amount: £{result.invoice.net_amount:.2f} (ex-VAT)")
                lines.append(f"   PDF: {Path(result.pdf_path).name}")

            lines.append(f"   Status: {result.get_status_summary()}")
            lines.append("")

            lines.append("   Validations:")
            for validation in result.validations:
                symbol = "✓" if validation.passed else "✗"
                lines.append(f"      {symbol} {validation.check_name}: {validation.message}")

            if result.errors:
                lines.append("\n   Errors:")
                for error in result.errors:
                    lines.append(f"      - {error}")

            if result.warnings:
                lines.append("\n   Warnings:")
                for warning in result.warnings:
                    lines.append(f"      - {warning}")

            lines.append("")

        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
