"""
Configuration settings for invoice automation.
"""
from pathlib import Path
from decimal import Decimal
import yaml


class Config:
    """Configuration container for invoice automation."""

    def __init__(self, config_path: Path = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file (optional)
        """
        # Default values
        self.maintenance_workbook = "example-files/Maintenance PO's - April 2025 (EXAMPLE).xlsx"
        self.cost_centre_summary = "example-files/Cost Centre Summary (Addresses & Nominal Codes).xlsx"
        self.invoices_input_dir = "invoices_to_process"
        self.output_dir = "output"
        self.backup_dir = "backups"

        # Validation thresholds
        self.store_match_threshold = 70
        self.high_confidence_threshold = 80
        self.quote_authorization_threshold = Decimal('200.00')

        # Processing options
        self.create_backup = True
        self.log_level = "INFO"

        # Load from file if provided
        if config_path and Path(config_path).exists():
            self.load_from_file(config_path)

    def load_from_file(self, config_path: Path):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Load paths
        if 'paths' in config_data:
            paths = config_data['paths']
            self.maintenance_workbook = paths.get('maintenance_workbook', self.maintenance_workbook)
            self.cost_centre_summary = paths.get('cost_centre_summary', self.cost_centre_summary)
            self.invoices_input_dir = paths.get('invoices_input_dir', self.invoices_input_dir)
            self.output_dir = paths.get('output_dir', self.output_dir)
            self.backup_dir = paths.get('backup_dir', self.backup_dir)

        # Load validation settings
        if 'validation' in config_data:
            validation = config_data['validation']
            self.store_match_threshold = validation.get('store_match_threshold', self.store_match_threshold)
            self.high_confidence_threshold = validation.get('high_confidence_threshold', self.high_confidence_threshold)
            self.quote_authorization_threshold = Decimal(str(validation.get('quote_authorization_threshold', '200.00')))

        # Load processing options
        if 'processing' in config_data:
            processing = config_data['processing']
            self.create_backup = processing.get('create_backup', self.create_backup)
            self.log_level = processing.get('log_level', self.log_level)
