"""
Tests for project organization and basic functionality.
"""
import unittest
import os
import sys
import subprocess

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestProjectOrganization(unittest.TestCase):
    """Test cases for the overall organization and structure of the XML parsing utility."""

    def test_essential_modules_present(self):
        """
        Tests for the presence of essential modules within the ra_d_ps package,
        verifying that the core components of the application are in place.
        """
        base_path = 'src/ra_d_ps'
        expected_files = ['__init__.py', 'parser.py', 'utils.py', 'gui.py', 'config.py']
        for f in expected_files:
            self.assertTrue(os.path.isfile(os.path.join(base_path, f)))

    def test_cli_and_main_files_exist(self):
        """
        Tests for the existence of cli.py and main.py at the root level,
        ensuring that the command-line interface and main entry point are accessible.
        """
        self.assertTrue(os.path.isfile('cli.py'))
        self.assertTrue(os.path.isfile('main.py'))


class TestFunctionality(unittest.TestCase):
    """Test cases for the functionality of the XML parsing utility."""

    def test_imports(self):
        """
        Test that essential functions can be imported from the package.
        """
        # Test that functions can be imported without raising ImportError
        try:
            # pylint: disable=import-outside-toplevel,unused-import
            from ra_d_ps import (
                parse_multiple,
                export_excel,
                convert_parsed_data_to_ra_d_ps_format,
                NYTXMLGuiApp
            )
            # If we reach here, imports succeeded
        except ImportError as e:
            self.fail(f"Failed to import essential functions: {e}")

    def test_cli_help(self):
        """
        Test that the CLI help command runs without errors.
        """
        # Test CLI by running it as a subprocess
        try:
            result = subprocess.run(
                ['python3', 'cli.py', '--help'],
                capture_output=True, text=True, check=True
            )
            self.assertEqual(result.returncode, 0)
        except subprocess.CalledProcessError as e:
            self.fail(f"CLI help command failed with exit code {e.returncode}")

    def test_main_script_help(self):
        """
        Test that the main.py script runs with --help argument.
        """
        try:
            subprocess.check_output(['python3', 'main.py', '--help'])
        except subprocess.CalledProcessError as e:
            self.fail(f"main.py --help failed with exit code {e.returncode}")


if __name__ == "__main__":
    unittest.main()
