"""
formatter.py - Report generation and export

Generates markdown and PDF reports from agent outputs.
Fixed PDF generation to handle markdown content properly.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
import re


class AgentReport:
    """
    Creates formatted reports from agent outputs.
    Supports both Markdown and PDF export.
    """
    
    def __init__(self, report_name="agent_report"):
        """
        Initialize report generator.
        
        Args:
            report_name: Base name for the report file (without extension)
        """
        self.report_name = report_name
        self.agent_outputs = {}

    def add_agent_output(self, agent_type, output):
        """
        Add an agent's output to the report.
        
        Args:
            agent_type: Type of agent (e.g., "product_manager")
            output: The agent's output text
        """
        self.agent_outputs[agent_type] = output

    def save(self, to_pdf=False):
        """
        Save the report to file.
        
        Args:
            to_pdf: If True, save as PDF. If False, save as Markdown.
            
        Returns:
            Path to the saved file
        """
        markdown_content = self._generate_markdown()

        if to_pdf:
            self._save_as_pdf(markdown_content)
            return f"{self.report_name}.pdf"
        else:
            with open(f"{self.report_name}.md", "w", encoding="utf-8") as f:
                f.write(markdown_content)
            return f"{self.report_name}.md"

    def _generate_markdown(self):
        """
        Generate markdown content from agent outputs.
        
        Returns:
            Formatted markdown string
        """
        content = f"# {self.report_name.replace('_', ' ').title()}\n\n"
        for agent_type, output in self.agent_outputs.items():
            content += f"## {agent_type.replace('_', ' ').title()}\n\n"
            content += f"{output}\n\n"
            content += "---\n\n"  # Add separator between sections
        return content

    def _save_as_pdf(self, markdown_content):
        """
        Save report as PDF with proper formatting.
        
        Converts markdown to PDF using ReportLab.
        Handles headers, paragraphs, and special characters properly.
        
        Args:
            markdown_content: Markdown formatted text
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                f"{self.report_name}.pdf",
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get default styles and create custom ones
            styles = getSampleStyleSheet()
            
            # Custom title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=HexColor('#1f77b4'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Custom heading style
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=HexColor('#2ca02c'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Custom body style
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                leading=14,
                spaceAfter=12,
                alignment=TA_LEFT
            )
            
            # Build story (content elements)
            story = []
            
            # Split content into lines
            lines = markdown_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    # Empty line - add small space
                    story.append(Spacer(1, 0.1 * inch))
                    continue
                
                # Escape special characters for ReportLab
                line = self._escape_for_pdf(line)
                
                # Handle markdown headers
                if line.startswith('# '):
                    # Main title (H1)
                    text = line[2:].strip()
                    story.append(Paragraph(text, title_style))
                    story.append(Spacer(1, 0.3 * inch))
                    
                elif line.startswith('## '):
                    # Section heading (H2)
                    text = line[3:].strip()
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(text, heading_style))
                    
                elif line.startswith('### '):
                    # Subsection heading (H3)
                    text = line[4:].strip()
                    story.append(Paragraph(f"<b>{text}</b>", body_style))
                    
                elif line.startswith('---'):
                    # Horizontal rule - add page break or large space
                    story.append(Spacer(1, 0.3 * inch))
                    
                elif line.startswith('- ') or line.startswith('* '):
                    # Bullet point
                    text = line[2:].strip()
                    story.append(Paragraph(f"• {text}", body_style))
                    
                elif re.match(r'^\d+\.', line):
                    # Numbered list
                    story.append(Paragraph(line, body_style))
                    
                else:
                    # Regular paragraph
                    # Handle bold and italic markdown
                    line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
                    line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', line)
                    line = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', line)
                    
                    story.append(Paragraph(line, body_style))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            # If PDF generation fails, provide helpful error
            raise Exception(f"PDF generation failed: {str(e)}. Check that reportlab is installed correctly.")
    
    def _escape_for_pdf(self, text):
        """
        Escape special characters for ReportLab PDF generation.
        
        Args:
            text: Input text
            
        Returns:
            Escaped text safe for PDF
        """
        # Replace characters that cause issues in ReportLab
        replacements = {
            '&': '&',
            '<': '<',
            '>': '>',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
