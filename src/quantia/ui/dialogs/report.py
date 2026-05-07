"""Report Generation Dialog.

Builds an HTML or PDF report from the current session's data summary,
script, and statistical results.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class ReportDialog(QDialog):
    """Dialog for configuring and generating analysis reports."""

    def __init__(
        self,
        df,
        script_text: str,
        results_html: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Generate Report")
        self.setMinimumWidth(420)
        self._df = df
        self._script_text = script_text
        self._results_html = results_html

        layout = QVBoxLayout(self)

        # Title
        layout.addWidget(QLabel("Report Title:"))
        self._title_edit = QLineEdit("Quantia Analysis Report")
        layout.addWidget(self._title_edit)

        # Sections
        sec_group = QGroupBox("Include Sections")
        sec_layout = QVBoxLayout()
        self.chk_summary = QCheckBox("Dataset Summary")
        self.chk_summary.setChecked(True)
        sec_layout.addWidget(self.chk_summary)

        self.chk_script = QCheckBox("Executed Python Script")
        self.chk_script.setChecked(True)
        sec_layout.addWidget(self.chk_script)

        self.chk_results = QCheckBox("Statistical Results")
        self.chk_results.setChecked(True)
        sec_layout.addWidget(self.chk_results)

        sec_group.setLayout(sec_layout)
        layout.addWidget(sec_group)

        # Format
        fmt_group = QGroupBox("Report Output")
        fmt_layout = QVBoxLayout()
        
        fmt_layout.addWidget(QLabel("Theme:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems([
            "Modern (Default)", 
            "Academic (APA 7th)", 
            "IEEE",
            "The Economist", 
            "Nature", 
            "Science", 
            "Dark Mode"
        ])
        fmt_layout.addWidget(self.cmb_theme)

        fmt_layout.addWidget(QLabel("File Format:"))
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["HTML Document (.html)", "PDF Document (.pdf)"])
        fmt_layout.addWidget(self.cmb_format)
        
        fmt_group.setLayout(fmt_layout)
        layout.addWidget(fmt_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._generate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_html(self) -> str:
        """Build the full HTML report string."""
        title = self._title_edit.text() or "Quantia Analysis Report"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        theme = self.cmb_theme.currentText()

        css_modern = """
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1E293B; background: #fff; margin: 40px; line-height: 1.6; }
            h1 { color: #0F172A; border-bottom: 3px solid #3B82F6; padding-bottom: 8px; }
            h2 { color: #1E40AF; margin-top: 32px; page-break-before: always; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #334155; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; }
            th, td { text-align: left; padding: 5px 10px; border-bottom: 1px solid #E2E8F0; }
            th { background: #F1F5F9; font-weight: 600; color: #475569; border-bottom: 2px solid #CBD5E1; }
            tr:nth-child(even) { background: #F8FAFC; }
            pre { background: #1E293B; color: #E2E8F0; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 12px; font-family: 'Cascadia Code', Consolas, monospace; white-space: pre-wrap; word-wrap: break-word; }
            hr { border: none; border-top: 1px solid #CBD5E1; margin: 24px 0; }
            .meta { color: #64748B; font-size: 13px; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { body { margin: 0; } pre { background: #F1F5F9 !important; color: #1E293B !important; } }
        </style>
        """

        css_apa = """
        <style>
            body { font-family: 'Times New Roman', Times, serif; color: #000; background: #fff; margin: 40px; line-height: 2.0; }
            h1 { color: #000; text-align: center; font-weight: bold; margin-bottom: 24px; border: none; }
            h2 { color: #000; font-weight: bold; margin-top: 32px; page-break-before: always; text-align: center; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #000; font-weight: bold; font-style: italic; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; border-top: 2px solid #000; border-bottom: 2px solid #000; }
            th, td { text-align: left; padding: 5px 10px; border-bottom: none; }
            th { border-bottom: 1px solid #000; font-weight: normal; background: none; color: #000; }
            tr:nth-child(even) { background: none; }
            pre { background: #fff; color: #000; padding: 16px; border: 1px solid #000; overflow-x: auto; font-size: 12px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; }
            hr { border: none; border-top: 1px solid #000; margin: 24px 0; }
            .meta { color: #000; font-size: 13px; text-align: center; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { body { margin: 0; } }
        </style>
        """

        css_ieee = """
        <style>
            body { font-family: 'Times New Roman', Times, serif; color: #000; background: #fff; margin: 40px; line-height: 1.2; font-size: 14px; }
            h1 { color: #000; text-align: center; font-size: 24px; margin-bottom: 24px; border: none; }
            h2 { color: #000; font-variant: small-caps; text-align: center; margin-top: 24px; page-break-before: always; border: none; font-size: 16px; letter-spacing: 1px; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #000; font-style: italic; font-size: 14px; margin-top: 16px; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; border-top: 2px solid #000; border-bottom: 2px solid #000; }
            th, td { text-align: center; padding: 4px; border-bottom: none; }
            th { border-bottom: 1px solid #000; font-weight: bold; background: none; color: #000; text-transform: uppercase; font-size: 10px; }
            tr:nth-child(even) { background: none; }
            pre { background: #fff; color: #000; padding: 12px; border: 1px solid #000; overflow-x: auto; font-size: 11px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; margin-top: 16px; }
            hr { border: none; border-top: 1px solid #000; margin: 24px 0; }
            .meta { color: #000; font-size: 12px; text-align: center; font-style: italic; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { body { margin: 0; } }
        </style>
        """

        css_economist = """
        <style>
            body { font-family: Arial, sans-serif; color: #014D64; background: #D5E4EB; margin: 40px; line-height: 1.6; }
            h1 { color: #DB444B; border-bottom: 4px solid #DB444B; padding-bottom: 8px; font-weight: bold; }
            h2 { color: #01A2D9; margin-top: 32px; page-break-before: always; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #014D64; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; background: #fff; }
            th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #6794A7; }
            th { background: #014D64; font-weight: bold; color: #fff; border: none; }
            tr:nth-child(even) { background: #F2F7F9; }
            pre { background: #fff; color: #014D64; padding: 16px; border-left: 4px solid #DB444B; overflow-x: auto; font-size: 12px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; }
            hr { border: none; border-top: 2px solid #01A2D9; margin: 24px 0; }
            .meta { color: #014D64; font-size: 13px; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { body { margin: 0; background: #fff; } table { border: 1px solid #014D64; } }
        </style>
        """

        css_nature = """
        <style>
            body { font-family: Arial, sans-serif; color: #333333; background: #FFFFFF; margin: 40px; line-height: 1.6; }
            h1 { color: #E64B35; border-bottom: 2px solid #333333; padding-bottom: 8px; font-weight: bold; }
            h2 { color: #4DBBD5; margin-top: 32px; page-break-before: always; border-bottom: 1px solid #CCCCCC; padding-bottom: 4px; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #333333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; border-bottom: 2px solid #333333; border-top: 2px solid #333333; }
            th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #EEEEEE; }
            th { background: #F9F9F9; font-weight: bold; color: #333333; border-bottom: 1px solid #333333; }
            tr:nth-child(even) { background: #FFFFFF; }
            pre { background: #F5F5F5; color: #333333; padding: 16px; border-left: 3px solid #E64B35; overflow-x: auto; font-size: 12px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; }
            hr { border: none; border-top: 1px solid #333333; margin: 24px 0; }
            .meta { color: #666666; font-size: 13px; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { body { margin: 0; } }
        </style>
        """

        css_science = """
        <style>
            body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #222222; background: #FFFFFF; margin: 40px; line-height: 1.5; }
            h1 { color: #3B4992; border-bottom: 1px solid #3B4992; padding-bottom: 8px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
            h2 { color: #EE0000; margin-top: 32px; page-break-before: always; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #222222; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; }
            th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #DDDDDD; }
            th { background: #FFFFFF; font-weight: bold; color: #3B4992; border-bottom: 2px solid #3B4992; border-top: 2px solid #3B4992; }
            tr:nth-child(even) { background: #FAFAFA; }
            pre { background: #FFFFFF; color: #222222; padding: 16px; border: 1px solid #DDDDDD; border-left: 4px solid #EE0000; overflow-x: auto; font-size: 12px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; }
            hr { border: none; border-top: 1px solid #DDDDDD; margin: 24px 0; }
            .meta { color: #888888; font-size: 13px; font-style: italic; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { body { margin: 0; } }
        </style>
        """

        css_dark = """
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #E2E8F0; background: #0F172A; margin: 40px; line-height: 1.6; }
            h1 { color: #F8FAFC; border-bottom: 3px solid #3B82F6; padding-bottom: 8px; }
            h2 { color: #60A5FA; margin-top: 32px; page-break-before: always; }
            h2:first-of-type { page-break-before: avoid; }
            h3 { color: #94A3B8; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 12px; }
            th, td { text-align: left; padding: 5px 10px; border-bottom: 1px solid #334155; }
            th { background: #1E293B; font-weight: 600; color: #F8FAFC; border-bottom: 2px solid #475569; }
            tr:nth-child(even) { background: #0B1120; }
            pre { background: #000000; color: #10B981; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 12px; font-family: 'Cascadia Code', Consolas, monospace; white-space: pre-wrap; word-wrap: break-word; }
            hr { border: none; border-top: 1px solid #334155; margin: 24px 0; }
            .meta { color: #94A3B8; font-size: 13px; }
            .result-section { page-break-before: always; }
            .result-section:first-child { page-break-before: avoid; }
            @media print { 
                body { background: #fff !important; color: #000 !important; margin: 0; } 
                h1 { color: #000 !important; border-color: #000 !important; }
                h2 { color: #333 !important; }
                th { background: #eee !important; color: #000 !important; border-color: #000 !important; }
                td { border-color: #ccc !important; }
                tr:nth-child(even) { background: #fff !important; }
                pre { background: #f9f9f9 !important; color: #000 !important; border: 1px solid #ccc !important; }
            }
        </style>
        """

        theme_map = {
            "Modern (Default)": css_modern,
            "Academic (APA 7th)": css_apa,
            "IEEE": css_ieee,
            "The Economist": css_economist,
            "Nature": css_nature,
            "Science": css_science,
            "Dark Mode": css_dark
        }
        
        css = theme_map.get(theme, css_modern)

        parts = [
            f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>{css}</head><body>",
            f"<h1>{title}</h1>",
            f"<p class='meta'>Generated on {now} by Quantia</p>",
        ]

        if self.chk_summary.isChecked() and self._df is not None:
            df = self._df
            if hasattr(df, 'to_pandas'):
                df = df.to_pandas()
            dtypes = df.dtypes.value_counts()
            dtype_str = ", ".join(f"{v} {k}" for k, v in dtypes.items())
            parts.append("<h2>Dataset Summary</h2>")
            parts.append(f"<p><b>Rows:</b> {len(df):,} &nbsp; <b>Columns:</b> {len(df.columns)}</p>")
            parts.append(f"<p><b>Column types:</b> {dtype_str}</p>")
            desc = df.describe(include="all").round(3).T
            parts.append(desc.to_html(classes="table"))

        if self.chk_script.isChecked() and self._script_text.strip():
            parts.append("<h2>Python Script</h2>")
            escaped = (
                self._script_text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            parts.append(f"<pre>{escaped}</pre>")

        if self.chk_results.isChecked() and self._results_html.strip():
            parts.append("<h2>Statistical Results</h2>")
            parts.append(self._results_html)

        parts.append("</body></html>")
        return "\n".join(parts)

    def _generate(self) -> None:
        """Generate the report file."""
        fmt = self.cmb_format.currentText()
        is_pdf = "PDF" in fmt

        if is_pdf:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", "report.pdf", "PDF Files (*.pdf)"
            )
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", "report.html", "HTML Files (*.html)"
            )

        if not path:
            return

        html = self._build_html()

        try:
            if is_pdf:
                self._save_pdf(path, html)
            else:
                Path(path).write_text(html, encoding="utf-8")

            QMessageBox.information(self, "Report Saved", f"Report saved to:\n{path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save report:\n{e}")

    def _save_pdf(self, path: str, html: str) -> None:
        """Render HTML to PDF using Edge headless for browser-quality output."""
        import shutil
        import subprocess
        import tempfile

        # Write HTML to a temp file for the browser to read
        tmp_dir = tempfile.mkdtemp()
        tmp_html = str(Path(tmp_dir) / "report.html")
        Path(tmp_html).write_text(html, encoding="utf-8")

        # Find Edge (guaranteed on Windows 10+)
        edge_paths = [
            shutil.which("msedge"),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        edge_exe = None
        for p in edge_paths:
            if p and Path(p).exists():
                edge_exe = p
                break

        if edge_exe is None:
            # Fallback: try Chrome
            chrome_paths = [
                shutil.which("chrome"),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            for p in chrome_paths:
                if p and Path(p).exists():
                    edge_exe = p
                    break

        if edge_exe is None:
            QMessageBox.warning(
                self, "Browser Not Found",
                "Could not find Edge or Chrome.\n"
                "Please open the HTML report in your browser and print to PDF from there."
            )
            # Save as HTML instead
            Path(path.replace(".pdf", ".html")).write_text(html, encoding="utf-8")
            return

        try:
            result = subprocess.run(
                [
                    edge_exe,
                    "--headless",
                    "--disable-gpu",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={path}",
                    tmp_html,
                ],
                capture_output=True,
                timeout=30,
            )
        finally:
            # Clean up temp file
            try:
                import shutil as sh
                sh.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

