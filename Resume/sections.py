from pylatex import escape_latex
from string import Template
from datetime import datetime
from typing import List
import json
import textwrap
import logging
from pathlib import Path

from rich import print
from rich.syntax import Syntax

EMPTY_ITEMIZE = textwrap.dedent("""\
    \\begin{itemize}[nosep]\item[]
    \\end{itemize}
    """)


class MetaData:
    colors = {
        "main_color": "MaterialDeepOrange",
        "sec_color": "MaterialGrey",
        "custom": [],
    }

    def __init__(self, data: dict) -> None:
        self.name = data.get("name")
        self.position = data.get("label")
        self.email = data.get("email")
        self.phone = data.get("phone")
        self.phone_fmt = data.get("phoneFormat")
        self.set_colors()

    def set_colors(self, colors: dict = None):
        if not colors:
            colors = MetaData.colors

        self.main_color = colors["main_color"]
        self.sec_color = colors["sec_color"]

    @staticmethod
    def add_custom_color_command(color_command: str):
        MetaData.colors["custom"].append(color_command)

    def to_latex(self):
        if (not self.main_color) and (not self.sec_color):
            self.main_color = MetaData.colors["main_color"]
            self.sec_color = MetaData.colors["sec_color"]

        template_str = """\
            \\newcommand{\\AuthorName}{$name}
            \\newcommand{\\postapp}{$position}
            \\newcommand{\\email}{$email}
            \\newcommand{\\phone}{$phone}
            \\newcommand{\\PhoneFormatted}{$phone_fmt}
            
            \\newcommand{\\maincolor}{$main_color}
            \\newcommand{\\seccolor}{$sec_color}
            """

        template_str = textwrap.dedent(template_str)
        if len(MetaData.colors["custom"]):
            for command in MetaData.colors["custom"]:
                command_str = f"{command}\n"
                template_str += command_str

        template = Template(template_str)
        data = {
            "name": self.name,
            "position": self.position,
            "email": self.email,
            "phone": self.phone,
            "phone_fmt": self.phone_fmt,
            "main_color": self.main_color,
            "sec_color": self.sec_color,
        }
        return template.safe_substitute(data)


class ProfileLink:
    # TODO: Add default configuration for unhandled files
    # TODO: Proper Log Error Message for Unpresent Icon
    social_profs_path = Path("./resources/data/social_profiles.json")
    default_meta = {"color": "MaterialGrey700", "command": "\\ProfileLink"}

    def __init__(self, network: str, username: str, url: str) -> None:
        self.network = network.lower()
        self.username = escape_latex(username)
        self.url = url
        self.data = {  # schema defined here
            "username": self.username,
            "url": self.url,
            "network": self.network,
            "file": "",
            "color": "",
            "custom_color_command": "",
            "command": "",
        }

    def get_meta(self) -> dict:
        nw = self.network
        with open(ProfileLink.social_profs_path, "r") as f:
            data = json.load(f)

        if nw in data["custom_icons"].keys():
            meta = data["custom_icons"][nw]
            return meta

        elif nw in data["fontawesome"].keys():
            meta = data["fontawesome"][nw]
            if not meta:
                return ProfileLink.default_meta

            return meta

        else:
            raise KeyError(
                f"Icon for `{self.network}` not found in LaTeX FontAwesome or Custom Database"
            )

    def to_latex(self) -> str:
        meta = self.get_meta()
        data = self.data

        if not meta:
            logging.warning(f"No metadata available for {self.network}")

        else:
            for k in meta.keys():
                data[k] = meta[k]

            template_str = """\
                $command
                {$color}
                {$network}
                {$url}
                {$username}
                \\LinkSep
                %
                """

            if data.get("custom_color_command"):
                MetaData.add_custom_color_command(data["custom_color_command"])

            template = Template(textwrap.dedent(template_str))
            logging.info(f"Created `ProfileLink` for {self.network}")
            return template.safe_substitute(data)


class Experience:
    _config = {"datefmt": "%b %Y", "show_summary": False, "link_website": False}

    def __init__(
        self,
        company: str = None,
        position: str = None,
        website: str = None,
        startDate: str = None,
        endDate: str = None,
        summary: str = None,
        highlights: List[str] = None,
    ) -> None:

        self.company = company
        self.position = position
        self.website = website
        self.startDate = startDate
        self.endDate = endDate
        self.summary = summary
        self.highlights = highlights

    def parse_dates(self):
        self.start = datetime.strptime(self.startDate, "%Y-%m-%d")
        self.end = datetime.strptime(self.endDate, "%Y-%m-%d")

    def to_latex(self):
        self.parse_dates()
        config = Experience._config

        if config["link_website"]:
            work_place = "\\href{" + self.website + "}{" + self.company + "}"
        else:
            work_place = f"{self.company}"

        template_str = """\
            \\Experience
            {$position}
            {$start to $end}
            {$work_place}
            """
        template = Template(textwrap.dedent(template_str))
        data = {
            "position": self.position,
            "start": self.start.strftime(config["datefmt"]),
            "end": self.end.strftime(config["datefmt"]),
            "work_place": work_place,
        }
        filled = template.safe_substitute(data)

        if len(self.highlights):
            highlights_str = """\
                \\begin{itemize}
                \t$highlights  
                \\end{itemize}
                """
            highlights_template = Template(textwrap.dedent(highlights_str))
            filled += highlights_template.safe_substitute({
                "highlights": "\n\t".join(
                    [f"\\item {escape_latex(i)}" for i in self.highlights]
                ),
            })
            
            return filled
            
        return filled + "\n"


class Education:
    _config = {
        "datefmt": "%Y",
    }

    def __init__(
        self,
        institution: str = None,
        area: str = None,
        studyType: str = None,
        startDate: str = None,
        endDate: str = None,
        gpa: str = None,
        summary: str = None,
        highlights: List[str] = None,
        url: str = None,
    ) -> None:

        self.institution = escape_latex(institution)
        self.area = escape_latex(area)
        self.studyType = studyType
        self.startDate = startDate
        self.endDate = endDate
        self.gpa = gpa
        self.url = url
        self.summary = escape_latex(summary)
        self.highlights = highlights

    def parse_dates(self):
        self.start = datetime.strptime(self.startDate, "%Y-%m-%d")
        self.end = datetime.strptime(self.endDate, "%Y-%m-%d")

    def to_latex(self):
        self.parse_dates()
        config = Education._config

        template_str = """\
            \\Education
            {$studyType}
            {$start to $end}
            {$institution}
            ${summary}.
            """
        
        template = Template(textwrap.dedent(template_str))
        data = {
            "studyType": self.studyType,
            "area": self.area,
            "gpa": self.gpa,
            "start": self.start.strftime(config["datefmt"]),
            "end": self.end.strftime(config["datefmt"]),
            "institution": self.institution,
            "summary": self.summary
        }
        filled = template.safe_substitute(data)
        
        if len(self.highlights):
            highlights_str = """\
                \\begin{itemize}
                \t$highlights  
                \\end{itemize}
                """
            highlights_template = Template(textwrap.dedent(highlights_str))
            filled += highlights_template.safe_substitute({
                "highlights": "\n\t".join(
                    [f"\\item {escape_latex(i)}" for i in self.highlights]
                ),
            })
            return filled

        
        return filled + EMPTY_ITEMIZE

class TechnicalSkill:
    def __init__(
        self,
        name: str = None,
        level: str = None,
        keywords: List[str] = None,
    ) -> None:

        self.name = name
        self.level = level
        self.keywords = keywords

    def to_latex(self):
        template_str = "\\ItemSkill{$name} $items\n"
        template = Template(template_str)
        data = {
            "name": escape_latex(self.name),
            "items": ", ".join([i for i in self.keywords]),
        }
        return template.safe_substitute(data)


class Project:
    _config = {"datefmt": "%b %Y"}

    def __init__(self, data: dict) -> None:
        self.name = escape_latex(data.get("name"))
        self.description = escape_latex(data.get("description"))
        self.highlights: List[str] = data.get("highlights")
        self.keywords = data.get("keywords")
        self.startDate = data.get("startDate")
        self.endDate = data.get("endDate")
        self.url = data.get("url")
        self.roles = data.get("roles")
        self.entity = data.get("entity")
        self.type = data.get("type")

    def parse_dates(self):
        self.start = datetime.strptime(self.startDate, "%Y-%m-%d")
        self.end = datetime.strptime(self.endDate, "%Y-%m-%d")

    def to_latex(self):
        self.parse_dates()
        config = Project._config

        template_str = """\
            \\ProjectHead
            {$name}
            {$start to $end}
            {$url}
            {$keywords}
            \\begin{itemize}
            \t$highlights
            \\end{itemize}
            """
        template = Template(textwrap.dedent(template_str))

        def list_to_string_itemize(x: List[str], latex_esc=True):
            if latex_esc:
                return "\n\t".join([f"\\item {escape_latex(i)}" for i in x])
            else:
                return "\n\t".join([f"\\item {i}" for i in x])

        data = {
            "name": self.name,
            "start": self.start.strftime(config["datefmt"]),
            "end": self.end.strftime(config["datefmt"]),
            "keywords": ", ".join(self.keywords),
            "url": self.url,
            "highlights": list_to_string_itemize(self.highlights),
        }
        return template.safe_substitute(data)


class Achievement:
    def __init__(self, data: dict) -> None:
        self.title: str = data.get("title")
        pass

    def to_latex(self):
        return "\t\\item " + self.title.strip()


def print_latex_syntax(code: str):
    syn = Syntax(code, lexer_name="latex", background_color="default")
    print(syn)
    # print("\n")


def test():
    def test_meta():
        data = {
            "name": "Ishaan Aditya",
            "label": "MLE",
            "picture": "",
            "email": "ishaanaditya.v@gmail.com",
            "phone": "916204507435",
            "phoneFormat": "(+91) 620 450 7435",
        }
        meta = MetaData(data)
        meta.set_colors()
        print_latex_syntax(meta.to_latex())

    def test_profile_link():
        data = {
            "network": "github",
            "username": "15H44N",
            "url": "http://www.github.com/15H44N",
        }
        p = ProfileLink(**data)
        print_latex_syntax(p.to_latex())

    def test_experience():
        data = {
            "company": "Axis Bank",
            "position": "Summer Intern",
            "website": "https://axisbank.com",
            "startDate": "2021-05-24",
            "endDate": "2021-07-16",
            "summary": "",
            "highlights": [
                "Worked in Analytics (It was NOT Real job)",
                "Made Spreadsheet, Document & PPT for no reason ",
                "Wasted Time, Grinded Leetcode Problems by night",
                "Awarded 'Volunteer of the Month'",
            ],
        }

        e = Experience(**data)
        print_latex_syntax(e.to_latex())

    def test_education():
        data = {
            "institution": "Birla Institue of Technology, Mesra",
            "area": "Electronics & Communication Engineering",
            "studyType": "Bachelor of Technology",
            "startDate": "2018-07-01",
            "endDate": "2022-04-01",
            "gpa": "7.98",
            "highlights": [
                "Served as Co-Coordinator of Finance & Sponsorship, Society for Data Science BIT Mesra",
                "Served as General Body Member, Dhwani Music Club, BIT Mesra",
            ],
        }

        ed = Education(**data)
        print_latex_syntax(ed.to_latex())

    def test_techskills():
        data = {
            "name": "Libraries & Frameworks",
            "level": "Noob",
            "keywords": [
                "Tensorflow",
                "PyTorch",
                "Selenium",
                "SKLearn",
                "Plotly",
                "FastAPI",
                "Pandas",
                "BeautifulSoup",
            ],
        }
        ts = TechnicalSkill(**data)
        print_latex_syntax(ts.to_latex())

    def test_projects():
        data = {
            "name": "Miss Direction",
            "description": "A mapping engine that misguides you",
            "highlights": [
                "Won award at AIHacks 2016",
                "Built by all women team of newbie programmers",
                "Using modern technologies such as GoogleMaps, Chrome Extension and Javascript",
            ],
            "keywords": ["GoogleMaps", "Chrome Extension", "Javascript"],
            "startDate": "2016-08-24",
            "endDate": "2016-08-24",
            "url": "missdirection.example.com",
            "roles": ["Team lead", "Designer"],
            "entity": "Smoogle",
            "type": "application",
        }

        proj = Project(data)
        print_latex_syntax(proj.to_latex())

    # running tests
    # test_profile_link()
    # test_experience()
    # test_education()
    # test_techskills()
    # test_projects()
    test_meta()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN,
        filename="./resume_creation.log",
        filemode="a",
        format="%(levelname)s - %(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
    test()