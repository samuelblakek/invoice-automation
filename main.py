"""
Main CLI entry point for invoice automation.
"""
import click
from pathlib import Path
import sys

# Add invoice_automation to path
sys.path.insert(0, str(Path(__file__).parent))

from invoice_automation.config.settings import Config
from invoice_automation.processors import ExcelReader, ExcelWriter
from invoice_automation.validators import InvoiceValidator
from invoice_automation.extractors import (
    AAWExtractor, CJLExtractor, AmazonExtractor, APSExtractor, GenericExtractor, PDFExtractionError
)
from invoice_automation.models import ValidationResult
from invoice_automation.reports.report_generator import ReportGenerator


def identify_supplier(pdf_path: Path, first_page_text: str) -> str:
    """Identify supplier from filename or PDF content."""
    filename_lower = pdf_path.name.lower()
    text_lower = first_page_text.lower()

    if 'aaw' in filename_lower or 'aaw national' in text_lower:
        return 'AAW'
    elif 'cjl' in filename_lower or 'cjl group' in text_lower:
        return 'CJL'
    elif 'amazon' in filename_lower or 'amazon business' in text_lower:
        return 'AMAZON'
    elif 'aps' in filename_lower or 'automatic protection' in text_lower:
        return 'APS'
    elif 'compco' in filename_lower or 'compco fire' in text_lower:
        return 'COMPCO'
    else:
        return 'GENERIC'


def extract_invoice(pdf_path: Path):
    """Extract invoice from PDF."""
    import pdfplumber

    # Read first page to identify supplier
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""

    supplier_type = identify_supplier(pdf_path, first_page_text)

    # Select extractor
    extractors = {
        'AAW': AAWExtractor(),
        'CJL': CJLExtractor(),
        'AMAZON': AmazonExtractor(),
        'APS': APSExtractor(),
        'COMPCO': GenericExtractor(),
        'GENERIC': GenericExtractor(),
    }

    extractor = extractors.get(supplier_type, GenericExtractor())
    return extractor.extract(pdf_path)


@click.group()
def cli():
    """Invoice Processing Automation CLI"""
    pass


@cli.command()
@click.option('--input-dir', type=click.Path(exists=True), required=True,
              help='Directory containing invoice PDFs')
@click.option('--config', type=click.Path(exists=True), default='config.yaml',
              help='Path to configuration file')
@click.option('--dry-run', is_flag=True,
              help='Run without making changes to Excel files')
def process(input_dir, config, dry_run):
    """Process invoices from a directory."""

    click.echo(f"\nInvoice Processing Automation")
    click.echo("=" * 60)

    # Load configuration
    config_path = Path(config) if Path(config).exists() else None
    cfg = Config(config_path)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")

    # Initialize components
    click.echo(f"Loading reference data...")
    excel_reader = ExcelReader(
        Path(cfg.maintenance_workbook),
        Path(cfg.cost_centre_summary)
    )

    click.echo(f"Initializing validator...")
    validator = InvoiceValidator(excel_reader, cfg.quote_authorization_threshold)

    # Get PDF files
    input_path = Path(input_dir)
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        click.echo(f"\nNo PDF files found in {input_dir}")
        return

    click.echo(f"Found {len(pdf_files)} invoice(s)\n")

    # Process each invoice
    results = []

    for pdf_file in pdf_files:
        click.echo(f"Processing: {pdf_file.name}")

        try:
            # Extract invoice
            invoice = extract_invoice(pdf_file)
            click.echo(f"  Supplier: {invoice.supplier_name}")
            click.echo(f"  Invoice #: {invoice.invoice_number}")
            click.echo(f"  PO #: {invoice.po_number}")
            click.echo(f"  Amount: £{invoice.net_amount:.2f}")

            # Validate
            result = validator.validate(invoice)
            results.append(result)

            # Display validation result
            if result.can_auto_update:
                click.echo(click.style(f"  Status: ✓ PASSED - Ready for auto-update", fg='green'))
            elif result.errors:
                click.echo(click.style(f"  Status: ✗ FAILED - {len(result.errors)} error(s)", fg='red'))
                for error in result.errors[:2]:
                    click.echo(click.style(f"    - {error}", fg='red'))
            else:
                click.echo(click.style(f"  Status: ⚠ WARNING - Needs review", fg='yellow'))

            # Update Excel if not dry-run and validation passed
            if not dry_run and result.can_auto_update:
                with ExcelWriter(Path(cfg.maintenance_workbook), create_backup=cfg.create_backup) as writer:
                    success = writer.update_po_record(
                        result.po_record.sheet_name,
                        result.po_record.row_index,
                        invoice.invoice_number,
                        invoice.net_amount,
                        validator.excel_reader.date_parser.get_today()
                    )
                    if success:
                        click.echo(f"  ✓ Updated Excel spreadsheet")

        except PDFExtractionError as e:
            click.echo(click.style(f"  Status: ✗ EXTRACTION FAILED - {str(e)}", fg='red'))
            result = ValidationResult.create_error(str(pdf_file), str(e))
            results.append(result)

        except Exception as e:
            click.echo(click.style(f"  Status: ✗ ERROR - {str(e)}", fg='red'))
            result = ValidationResult.create_error(str(pdf_file), str(e))
            results.append(result)

        click.echo("")

    # Generate reports
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(exist_ok=True)

    report_gen = ReportGenerator(results)

    # Summary
    summary = report_gen.generate_summary()
    click.echo(summary)

    # Save CSV
    csv_path = output_dir / f"invoice_summary_{validator.excel_reader.date_parser.get_today().strftime('%Y%m%d')}.csv"
    report_gen.save_summary_csv(csv_path)
    click.echo(f"\nSummary saved to: {csv_path}")

    # Save detailed report
    report_path = output_dir / f"invoice_report_{validator.excel_reader.date_parser.get_today().strftime('%Y%m%d')}.txt"
    report_gen.save_detailed_report(report_path)
    click.echo(f"Detailed report saved to: {report_path}")


@cli.command()
def version():
    """Show version information."""
    click.echo("Invoice Processing Automation v1.0.0")


if __name__ == '__main__':
    cli()
