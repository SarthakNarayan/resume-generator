#!/usr/bin/env python3
"""
Dynamic Resume Generator
Generates a professional resume PDF from structured data in input.txt
"""

import sys
import yaml
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, darkblue, grey
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Flowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas


class TwoColumnLine(Flowable):
    """Custom flowable for left-right aligned text on the same line"""

    def __init__(self, left_text, right_text, left_style, right_style):
        self.left_text = left_text
        self.right_text = right_text
        self.left_style = left_style
        self.right_style = right_style

    def draw(self):
        canvas = self.canv

        # Draw left text at x=0
        canvas.setFont(self.left_style["fontName"], self.left_style["fontSize"])
        canvas.setFillColor(self.left_style.get("textColor", black))
        canvas.drawString(0, 0, self.left_text)

        # Calculate right text position using the actual available width
        right_text_width = canvas.stringWidth(
            self.right_text, self.right_style["fontName"], self.right_style["fontSize"]
        )
        right_x = self.width - right_text_width

        # Draw right text
        canvas.setFont(self.right_style["fontName"], self.right_style["fontSize"])
        canvas.setFillColor(self.right_style.get("textColor", black))
        canvas.drawString(right_x, 0, self.right_text)

    def wrap(self, availWidth, availHeight):
        # Use the actual available width provided by ReportLab
        self.width = availWidth
        return (availWidth, 14)  # 14 points height for text


class ResumeGenerator:
    """Generate professional resume PDF from structured input data"""

    def __init__(
        self, input_file="resume_data.yaml", output_file="Generated_Resume.pdf"
    ):
        self.input_file = input_file
        self.output_file = output_file
        self.data = {}
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for the resume"""
        # Name style
        self.styles.add(
            ParagraphStyle(
                name="Name",
                parent=self.styles["Heading1"],
                fontSize=20,
                textColor=darkblue,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Contact info style
        self.styles.add(
            ParagraphStyle(
                name="Contact",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=black,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName="Helvetica",
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=black,
                spaceBefore=8,
                spaceAfter=1,
                fontName="Helvetica-Bold",
            )
        )

        # Job title style
        self.styles.add(
            ParagraphStyle(
                name="JobTitle",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=black,
                fontName="Helvetica-Bold",
                spaceAfter=2,
            )
        )

        # Company style
        self.styles.add(
            ParagraphStyle(
                name="Company",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=black,
                fontName="Helvetica-Bold",
                spaceAfter=2,
            )
        )

        # Date/Location style
        self.styles.add(
            ParagraphStyle(
                name="DateLocation",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=grey,
                fontName="Helvetica-Oblique",
                spaceAfter=4,
            )
        )

        # Description style (for regular text like skills)
        self.styles.add(
            ParagraphStyle(
                name="Description",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=black,
                fontName="Helvetica",
                leftIndent=0,
                spaceAfter=2,
            )
        )

        # Bullet point style with hanging indent
        from reportlab.pdfbase.pdfmetrics import stringWidth

        dash_space_width = stringWidth("- ", "Helvetica", 11)

        self.styles.add(
            ParagraphStyle(
                name="BulletPoint",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=black,
                fontName="Helvetica",
                leftIndent=dash_space_width,  # Exact width of "- " in this font/size
                firstLineIndent=-dash_space_width,  # Pull first line back to margin
                spaceAfter=2,
            )
        )

    def parse_input_file(self):
        """Parse the YAML file and extract structured data"""
        if not Path(self.input_file).exists():
            raise FileNotFoundError(f"Input file {self.input_file} not found!")

        with open(self.input_file, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

    def add_section_separator(self, story):
        """Add a horizontal line separator after section heading"""
        # story.append(Spacer(1, 0.02 * inch))
        story.append(HRFlowable(width="100%", thickness=0.5, color=black))
        story.append(Spacer(1, 0.08 * inch))

    def create_personal_section(self, story):
        """Create the personal information section"""
        if "personal" not in self.data:
            return

        personal = self.data["personal"]

        # Name
        if "name" in personal:
            name = Paragraph(personal["name"], self.styles["Name"])
            story.append(name)

        # Contact information
        contact_info = []
        if "email" in personal:
            contact_info.append(personal["email"])
        if "phone" in personal:
            contact_info.append(personal["phone"])
        if "location" in personal:
            contact_info.append(personal["location"])
        if "linkedin" in personal:
            contact_info.append(personal["linkedin"])
        if "github" in personal:
            contact_info.append(personal["github"])
        if "website" in personal:
            contact_info.append(personal["website"])

        if contact_info:
            contact_text = " • ".join(contact_info)
            contact = Paragraph(contact_text, self.styles["Contact"])
            story.append(contact)

        story.append(Spacer(1, 0.03 * inch))

    def create_experience_section(self, story):
        """Create the experience section"""
        if "experience" not in self.data or not self.data["experience"]:
            return

        story.append(Paragraph("PROFESSIONAL EXPERIENCE", self.styles["SectionHeader"]))
        self.add_section_separator(story)

        for exp in self.data["experience"]:
            # Company (left) - Location (right) line
            if "company" in exp and "location" in exp:
                company_location_line = TwoColumnLine(
                    left_text=exp["company"],
                    right_text=exp["location"],
                    left_style={
                        "fontName": "Helvetica-Bold",
                        "fontSize": 12,
                        "textColor": black,
                    },
                    right_style={
                        "fontName": "Helvetica",
                        "fontSize": 11,
                        "textColor": black,
                    },
                )
                story.append(company_location_line)
                story.append(Spacer(1, 0.02 * inch))

            # Title (left) - Date (right) line
            if "title" in exp and "duration" in exp:
                title_date_line = TwoColumnLine(
                    left_text=exp["title"],
                    right_text=exp["duration"],
                    left_style={
                        "fontName": "Helvetica-Oblique",
                        "fontSize": 11,
                        "textColor": black,
                    },
                    right_style={
                        "fontName": "Helvetica-Oblique",
                        "fontSize": 11,
                        "textColor": grey,
                    },
                )
                story.append(title_date_line)
                story.append(Spacer(1, 0.04 * inch))

            # Responsibilities
            if "responsibilities" in exp:
                for responsibility in exp["responsibilities"]:
                    description = Paragraph(
                        f"- {responsibility}", self.styles["BulletPoint"]
                    )
                    story.append(description)

            story.append(Spacer(1, 0.05 * inch))

    def create_education_section(self, story):
        """Create the education section"""
        if "education" not in self.data or not self.data["education"]:
            return

        story.append(Paragraph("EDUCATION", self.styles["SectionHeader"]))
        self.add_section_separator(story)

        for edu in self.data["education"]:
            # Institution (left) - Duration (right) line
            if "institution" in edu and "duration" in edu:
                institution_duration_line = TwoColumnLine(
                    left_text=edu["institution"],
                    right_text=edu["duration"],
                    left_style={
                        "fontName": "Helvetica-Bold",
                        "fontSize": 12,
                        "textColor": black,
                    },
                    right_style={
                        "fontName": "Helvetica",
                        "fontSize": 11,
                        "textColor": black,
                    },
                )
                story.append(institution_duration_line)
                story.append(Spacer(1, 0.02 * inch))

            # Degree (left) - Location (right) line
            if "degree" in edu and "location" in edu:
                degree_location_line = TwoColumnLine(
                    left_text=edu["degree"],
                    right_text=edu["location"],
                    left_style={
                        "fontName": "Helvetica-Oblique",
                        "fontSize": 11,
                        "textColor": black,
                    },
                    right_style={
                        "fontName": "Helvetica-Oblique",
                        "fontSize": 11,
                        "textColor": grey,
                    },
                )
                story.append(degree_location_line)
                story.append(Spacer(1, 0.05 * inch))

    def create_skills_section(self, story):
        """Create the skills section"""
        if "skills" not in self.data or not self.data["skills"]:
            return

        story.append(Paragraph("TECHNICAL SKILLS", self.styles["SectionHeader"]))
        self.add_section_separator(story)

        # Handle simple list of skills
        skills_text = ", ".join(self.data["skills"])
        skills_para = Paragraph(skills_text, self.styles["Description"])
        story.append(skills_para)

        story.append(Spacer(1, 0.1 * inch))

    def create_certifications_section(self, story):
        """Create the certifications section"""
        if "certifications" not in self.data or not self.data["certifications"]:
            return

        story.append(Paragraph("CERTIFICATIONS", self.styles["SectionHeader"]))
        self.add_section_separator(story)

        for cert in self.data["certifications"]:
            cert_para = Paragraph(f"• {cert}", self.styles["Description"])
            story.append(cert_para)

    def create_projects_section(self, story):
        """Create the projects section"""
        if "projects" not in self.data or not self.data["projects"]:
            return

        story.append(Paragraph("PROJECTS", self.styles["SectionHeader"]))

        for project in self.data["projects"]:
            # Project name
            if "name" in project:
                name = Paragraph(f"<b>{project['name']}</b>", self.styles["JobTitle"])
                story.append(name)

            # Description
            if "description" in project:
                desc = Paragraph(project["description"], self.styles["Description"])
                story.append(desc)

            # Technologies
            if "technologies" in project:
                tech = Paragraph(
                    f"<b>Technologies:</b> {project['technologies']}",
                    self.styles["Description"],
                )
                story.append(tech)

            # Link
            if "link" in project:
                link = Paragraph(
                    f"<b>Link:</b> {project['link']}", self.styles["Description"]
                )
                story.append(link)

            story.append(Spacer(1, 0.1 * inch))

    def generate_pdf(self):
        """Generate the complete resume PDF"""
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=letter,
            rightMargin=0.3 * inch,
            leftMargin=0.3 * inch,
            topMargin=0.2 * inch,
            bottomMargin=0.2 * inch,
        )

        story = []

        # Build the resume sections
        self.create_personal_section(story)
        self.create_experience_section(story)
        self.create_education_section(story)
        self.create_skills_section(story)
        self.create_certifications_section(story)
        self.create_projects_section(story)

        # Build PDF
        doc.build(story)
        print(f"Resume generated successfully: {self.output_file}")


def main():
    """Main function to generate resume"""
    generator = ResumeGenerator()

    try:
        print("Parsing input data...")
        generator.parse_input_file()

        print("Generating PDF...")
        generator.generate_pdf()

        print("Resume generation completed successfully!")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure resume_data.yaml exists with your resume data")
        return 1
    except Exception as e:
        print(f"Error generating resume: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
