class AgentReport:
    def __init__(self, report_name="agent_report"):
        self.report_name = report_name
        self.agent_outputs = {}

    def add_agent_output(self, agent_type, output):
        self.agent_outputs[agent_type] = output

    def save(self, to_pdf=False):
        markdown_content = self._generate_markdown()

        if to_pdf:
            self._save_as_pdf(markdown_content)
            return f"{self.report_name}.pdf"
        else:
            with open(f"{self.report_name}.md", "w") as f:
                f.write(markdown_content)
            return f"{self.report_name}.md"

    def _generate_markdown(self):
        content = f"# {self.report_name.replace('_', ' ').title()}\n\n"
        for agent_type, output in self.agent_outputs.items():
            content += f"## {agent_type.replace('_', ' ').title()}\n\n"
            content += f"{output}\n\n"
        return content

    def _save_as_pdf(self, markdown_content):
        import markdown
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        html_content = markdown.markdown(markdown_content)
        doc = SimpleDocTemplate(f"{self.report_name}.pdf", pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        for line in html_content.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 12))

        doc.build(story)
