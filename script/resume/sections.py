import json
import logging
import textwrap
from typing import ClassVar, Dict, List
from pathlib import Path
from string import Template
from datetime import datetime
from pylatex import escape_latex
import config


def fill_template(template: Template, values: dict, de_indent=True) -> str:
    if de_indent:
        # return textwrap.dedent(template.substitute(values))
        filled = template.substitute(values)
        res = []
        for line in filled.splitlines():
            res.append(line.strip())
        return "\n".join(res)

    else:
        return template.substitute(values)


class MetaData:
    colors: dict = {"main_color": "MaterialBlue", "secn_color": "MaterialGrey", "custom": []}

    def __init__(self, data: dict) -> None:
        self.name = data.get("name")
        self.position = data.get("label")
        self.email = data.get("email")
        self.phone = data.get("phone")
        self.phone_fmt = data.get("phoneFormat")
        self.summary = data.get('summary')
        self.set_colors()

    def set_colors(self, colors: dict = None) -> None:
        if not colors:
            colors = MetaData.colors

        self.main_color = colors.get("main_color")
        
        if 'secn_color' in colors.keys():
            self.secn_color = colors.get("secn_color")

        if 'sec_color' in colors.keys():
            self.secn_color = colors.get("sec_color")
        
    @staticmethod
    def add_custom_color_command(color_command: str):
        MetaData.colors["custom"].append(color_command)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "position": self.position,
            "phone_fmt": self.phone_fmt,
            "main_color": self.main_color,
            "secn_color": self.secn_color,
        }

    def to_latex(self) -> str:
        template_str = """
            \\newcommand{\\AuthorName}{$name}
            \\newcommand{\\PositionName}{$position}
            \\newcommand{\\email}{$email}
            \\newcommand{\\phone}{$phone}
            \\newcommand{\\PhoneFormatted}{$phone_fmt}
            
            \\newcommand{\\maincolor}{$main_color}
            \\newcommand{\\seccolor}{$secn_color}
        """
        
        summary_command = ""
        if self.summary:
            summary_command = "\\newcommand{\\SummaryText}\n{" + escape_latex(self.summary).strip() + "}"
        
        else:
            summary_command = "\\newcommand{\\SummaryText}{ }"
        
        if MetaData.colors["custom"]:
            for command in MetaData.colors["custom"]:
                command_str = f"{command}\n"
                template_str += command_str

        template = Template(template_str)
        data = self.to_dict()
        filled_text = fill_template(template, data).strip()

        text_to_include_after = """\
            \n
            \\newcommand{\\MainColorDark}{\\maincolor800}
            \\newcommand{\\SecColorDark}{\\seccolor800}
            \\newcommand{\\SecColorLight}{\\seccolor500}
            \\renewcommand{\\maketitle}{\\ResumeHeader}
            \n
        """

        filled_text += textwrap.dedent(text_to_include_after)
        filled_text += summary_command + "\n"

        return filled_text


class ProfileLinks:
    class profile_link:
        # TODO: Add default configuration for unhandled files
        # TODO: Proper Log Error Message for Unpresent Icon

        class default:
            color: str = "MaterialGrey700"
            command: str = "\\ProfileLink"
            default_meta: dict = {"color": color, "command": command}

        def __init__(self, data: dict, is_ending: bool = False) -> None:
            self.network = data.get("network", "").lower()
            self.username = escape_latex(data.get("username", ""))
            self.url = data.get("url", "")
            self.data = {  # schema defined here
                "username": self.username,
                "url": self.url,
                "network": self.network,
                "file": "",
                "color": "",
                "custom_color_command": "",
                "command": "",
            }
            self.is_ending = is_ending

        def get_meta(self) -> dict:
            network = self.network
            with open(config.SOCIAL_PROFILES_PATH, "r") as f:
                data = json.load(f)

            if network in data["custom_icons"].keys():
                meta = data["custom_icons"][network]
                return meta

            elif network in data["fontawesome"].keys():
                meta = data["fontawesome"][network]
                if not meta:
                    return self.default().default_meta
                return meta

            else:
                raise KeyError(
                    f"Icon for `{self.network}` not found in LaTeX-FA5 or Custom Database"
                )

        def to_latex(self) -> str:
            data = self.data
            try:
                meta = self.get_meta()

            except KeyError:
                logging.warning(f"No metadata available for {self.network}. Skipping...")
                return ""

            for key in meta.keys():
                data[key] = meta[key]

            template = Template(
                """\
                $command
                {$color}
                {$network}
                {$url}
                {$username}
                """
            )

            if data.get("custom_color_command"):
                MetaData.add_custom_color_command(data["custom_color_command"])

            logging.info(f"created ProfileLink for ({self.network})")
            filled = fill_template(template, data)

            if not self.is_ending:
                filled += "\\LinkSep\n%\n"

            return filled

    def __init__(self, profiles: List[dict]) -> None:
        self.profiles = profiles
        self.last_idx = len(profiles) - 1

    def to_latex(self) -> str:
        template = Template(
            textwrap.dedent(
                """\
                \\newcommand{\\InsertProfileLinks}
                {
                \\begin{center}
                $links
                \\end{center}
                }    
                """
            )
        )

        links_text = ""
        for idx, profile in enumerate(self.profiles):
            is_last = idx == self.last_idx
            links_text += self.profile_link(profile, is_last).to_latex()

        return fill_template(template, {"links": links_text})


class Experience:
    class experience:
        class options:
            show_summary: bool = False
            link_website: bool = False
            date_fmt: str = "%b %Y"
            seperator: str = "\n".join(["%", "\\bigskip", "%\n"])

        def __init__(self, data: dict, is_ending: bool = False) -> None:
            self.is_ending = is_ending
            self.company = data.get("company", "")
            self.website = data.get("website", "")
            self.endDate = data.get("endDate", "")
            self.summary = data.get("summary", "")
            self.location = data.get("location", "")
            self.position = data.get("position", "")
            self.startDate = data.get("startDate", "")
            self.highlights = data.get("highlights", "")
            self.parse_dates()

        def parse_dates(self):
            self.start = datetime.strptime(self.startDate, "%Y-%m-%d")
            self.end = datetime.strptime(self.endDate, "%Y-%m-%d")

        def to_latex(self) -> str:
            config_ = self.options()

            template = Template(
                """\
                \\Experience
                {$position}
                {$location}
                {$work_place}
                {$start to $end}
                """
            )

            highlights_template = Template(
                """\
                \\begin{itemize}
                \t$highlights  
                \\end{itemize}
                """
            )

            work_place = (
                "\\href{" + self.website + "}{" + self.company + "}"
                if config_.link_website
                else self.company
            )

            data = {
                "position": self.position,
                "location": self.location,
                "start": self.start.strftime(config_.date_fmt),
                "end": self.end.strftime(config_.date_fmt),
                "work_place": work_place,
            }

            filled = fill_template(template, data)

            if self.highlights:
                highlights_text = "\n\t".join(
                    [f"\\item {escape_latex(item)}" for item in self.highlights]
                )
                filled += fill_template(highlights_template, {"highlights": highlights_text})

            if not self.is_ending:
                filled += config_.seperator

            else:
                filled += "\n"
            
            logging.info(f"created Experience for ({self.company}, {self.position })")
            return filled

    def __init__(self, exp: List[dict]) -> None:
        self.experience_entries = exp
        self.last_idx = len(exp) - 1

    def to_latex(self) -> str:
        filled = ""
        for idx, experience_entry in enumerate(self.experience_entries):
            is_last = idx == self.last_idx
            filled += self.experience(experience_entry, is_last).to_latex()

        return filled


class Education:
    class education:
        class options:
            show_summary: bool = False
            link_website: bool = False
            date_fmt: str = "%b %Y"
            seperator: str = "\n".join(["%", "\\bigskip", "%\n"])

        def __init__(self, data: dict, is_ending: bool = False) -> None:
            self.url = data.get("url", "")
            self.area = data.get("area", "")
            self.endDate = data.get("endDate", "")
            self.summary = data.get("summary", "")
            self.location = data.get("location", "")
            self.startDate = data.get("startDate", "")
            self.studyType = data.get("studyType", "")
            self.highlights = data.get("highlights", "")
            self.institution = data.get("institution", "")
            self.is_ending = is_ending
            self.parse_dates()

        def parse_dates(self):
            self.start = datetime.strptime(self.startDate, "%Y-%m-%d")
            self.end = datetime.strptime(self.endDate, "%Y-%m-%d")

        def to_latex(self) -> str:
            config_ = self.options()
            template = Template(
                """\
                \\Education
                {$studyType}
                {$location}
                {$institution}
                {$start to $end}
                """
            )

            highlights_template = Template(
                textwrap.dedent(
                    """\
                    \\begin{itemize}
                    $highlights  
                    \\end{itemize}
                    """
                )
            )

            data = {
                "end": self.end.strftime(config_.date_fmt),
                "start": self.start.strftime(config_.date_fmt),
                "location": self.location,
                "studyType": self.studyType,
                "institution": self.institution,
            }

            filled = fill_template(template, data)

            if self.highlights:
                highlights_text = "\n".join(
                    [f"\\item {escape_latex(item)}" for item in self.highlights]
                )
                filled += fill_template(highlights_template, {"highlights": highlights_text})

            if not self.is_ending:
                filled += config_.seperator

            else:
                filled += "\n"
            
            logging.info(f"created Education for ({self.studyType}, {self.institution})")
            return filled

    def __init__(self, education: List[dict]) -> None:
        self.education_entries = education
        self.last_idx = len(education) - 1

    def to_latex(self) -> str:
        filled = ""
        for idx, education_entry in enumerate(self.education_entries):
            is_last = idx == self.last_idx
            filled += self.education(education_entry, is_last).to_latex()

        return filled


class Projects:
    class project:
        class options:
            show_summary: bool = False
            link_website: bool = False
            date_fmt: str = "%b %Y"
            seperator: str = "\n".join(["%", "\\bigskip", "%\n"])

        def __init__(self, data: dict, is_ending: bool = False) -> None:
            self.url = data.get("url")
            self.type = data.get("type")
            self.roles = data.get("roles")
            self.entity = data.get("entity")
            self.endDate = data.get("endDate")
            self.keywords = data.get("keywords")
            self.startDate = data.get("startDate")
            self.name = escape_latex(data.get("name"))
            self.highlights: List[str] = data.get("highlights")
            self.description = escape_latex(data.get("description"))
            self.is_ending = is_ending
            self.parse_dates()

        def parse_dates(self):
            self.start = datetime.strptime(self.startDate, "%Y-%m-%d")
            self.end = datetime.strptime(self.endDate, "%Y-%m-%d")

        def to_latex(self):
            def list_to_string_itemize(x: List[str], latex_esc=True):
                if latex_esc:
                    return "\n\t".join([f"\\item {escape_latex(i)}" for i in x])
                else:
                    return "\n\t".join([f"\\item {i}" for i in x])

            config_ = self.options()
            template = Template(
                """\
                \\Project
                {$name}
                {$domain_name}
                {$start to $end}
                {$url}
                {$keywords}
                """
            )

            highlights_template = Template(
                """\
                \\begin{itemize}
                \t$highlights
                \\end{itemize}
                """
            )

            data = {
                "url": self.url,
                "name": self.name,
                "domain_name": self.type,
                "keywords": ", ".join(self.keywords),
                "end": self.end.strftime(config_.date_fmt),
                "start": self.start.strftime(config_.date_fmt),
            }

            highlights_data = {
                "highlights": list_to_string_itemize(self.highlights),
            }

            filled = fill_template(template, data) + fill_template(
                highlights_template, highlights_data
            )

            if not self.is_ending:
                filled += config_.seperator

            else:
                filled += "\n"
            
            logging.info(f"created Project for ({self.name})")
            return filled

    def __init__(self, projects: List[dict]) -> None:
        self.projects = projects
        self.last_idx = len(projects) - 1

    def to_latex(self) -> str:
        filled = ""
        for idx, project in enumerate(self.projects):
            is_last = idx == self.last_idx
            filled += self.project(project, is_last).to_latex()

        return filled


class TechnicalSkills:
    class Skill:
        def __init__(self, data: dict) -> None:
            self.name = data.get("name", "")
            self.level = data.get("level", "")
            self.keywords = data.get("keywords", "")

        def to_latex(self):
            template = Template("\\ItemSkill{$name} $items\n")
            data = {
                "name": escape_latex(self.name),
                "items": ", \\ ".join([i for i in self.keywords]),
            }
            logging.info(f"created TechSkills for ({self.name})")
            return template.safe_substitute(data)

    def __init__(self, skills: List[dict]) -> None:
        self.skills = skills

    def to_latex(self) -> str:
        filled = "\\begin{ListSkills}\n"
        for skill in self.skills:
            filled = filled + "\t" + self.Skill(skill).to_latex()

        return filled + "\\end{ListSkills}\n"


class Achievements:
    class Achv:
        def __init__(self, data: dict) -> None:
            self.title: str = escape_latex(data.get("title"))

        def to_latex(self):
            return "\t\\item " + self.title.strip() + "\n"

    def __init__(self, achvs: List[dict]) -> None:
        self.achvs = achvs

    def to_latex(self) -> str:
        filled = "\\begin{AchievementList}\n"
        for achv in self.achvs:
            filled = filled + self.Achv(achv).to_latex()

        logging.info(f"created {len(self.achvs)} Achievements")
        return filled + "\\end{AchievementList}\n"
