from typing import List
from pylatex import escape_latex
from string import Template
import json
import logging
import textwrap
from datetime import datetime
import inspect
from rich import print

from rich.syntax import Syntax


class ProfileLink:
    def __init__(self, network: str, username: str, url: str) -> None:
        self.network = network
        self.username = username
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
        with open("../../resources/data/social_profiles.json", "r") as f:
            data = json.load(f)

        if nw in data["custom_icons"].keys():
            meta = data["custom_icons"][nw]
            return meta

        elif nw in data["fontawesome"].keys():
            meta = data["fontawesome"][nw]
            return meta

        else:
            pass

    def to_latex(self) -> str:
        meta = self.get_meta()
        data = self.data

        if not meta:
            logging.warning(f"No metadata available for {self.network}")

        else:
            for k in meta.keys():
                data[k] = meta[k]

            template_str = """\
                ${custom_color_command}
                $command
                {$color}
                {$network}
                {$url}
                {$username}
                \\LinkSep
                %
                """

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
            \\begin{itemize}
            \t$highlights  
            \\end{itemize}
            """
        template = Template(textwrap.dedent(template_str))
        data = {
            "position": self.position,
            "start": self.start.strftime(config["datefmt"]),
            "end": self.end.strftime(config["datefmt"]),
            "work_place": work_place,
            "highlights": "\n\t".join(
                [f"\\item {escape_latex(i)}" for i in self.highlights]
            ),
        }

        filled = template.safe_substitute(data)
        return filled


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
        highlights: List[str] = None,
    ) -> None:

        self.institution = institution
        self.area = area
        self.studyType = studyType
        self.startDate = startDate
        self.endDate = endDate
        self.gpa = gpa
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
            ${studyType} in $area with GPA \\textbf{${gpa}}.
            \\begin{itemize}
            \t$highlights
            \\end{itemize}
            """
        template = Template(textwrap.dedent(template_str))
        data = {
            "studyType": self.studyType,
            "area": self.area,
            "gpa": self.gpa,
            "start": self.start.strftime(config["datefmt"]),
            "end": self.end.strftime(config["datefmt"]),
            "institution": self.institution,
            "highlights": "\n\t".join(
                [f"\\item {escape_latex(i)}" for i in self.highlights]
            ),
        }

        filled = template.safe_substitute(data)
        return filled


class TechnicalSkills:
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
            "name": self.name,
            "items": ", ".join([escape_latex(i) for i in self.keywords]),
        }
        return template.safe_substitute(data)


class Project:
    # TODO: Write this class
    def __init__(self) -> None:
        pass


class Achievements:
    # TODO :Write this class
    def __init__(self) -> None:
        pass


def test():
    def print_latex_syntax(code: str):
        syn = Syntax(code, lexer_name="latex", background_color="default")
        print(syn)
        print("\n")

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
        ts = TechnicalSkills(**data)
        print_latex_syntax(ts.to_latex())

    # running tests
    test_profile_link()
    test_experience()
    test_education()
    test_techskills()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="../resume_creation.log",
        filemode="a",
        format="%(levelname)s - %(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
    test()