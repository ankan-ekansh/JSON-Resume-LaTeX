import sys
import json
import logging
import os
import subprocess
import textwrap
from re import sub
from textwrap import dedent, indent
from typing import List

import commentjson
import pylatex
from rich import print
from rich.console import Console
from rich.spinner import Spinner
from rich.syntax import Syntax
from pathlib import Path

from Resume.sections import (
    Achievement,
    Education,
    Experience,
    MetaData,
    ProfileLink,
    Project,
    TechnicalSkill,
)

LOGGING_LEVEL_MAP = {
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def print_latex_syntax(code: str):
    syn = Syntax(code, lexer_name="latex", background_color="default")
    print(syn, end="")


def print_json(data: dict):
    syn = Syntax(
        code=json.dumps(data, indent=2), lexer_name="json", background_color="default"
    )
    print(syn)
    print("\n")


def parse_json(path: Path = "./resume.jsonc") -> dict:
    with open(path, "r") as f:
        d = commentjson.load(f)
    return d


def create_resume(data: dict):
    """
    High Level Function to create Resume .tex and .pdf files from the `json` resume spec passed in. Uses helper functions and submodule classes for actual building of resume tex file

    Args:
        data (dict): [description]
    """

    def section_MetaData(data: dict):
        m = MetaData(data["basics"])
        m.set_colors(data["meta"])
        # print(m.to_latex())
        return m.to_latex()

    def section_ProfileLinks(profiles: List[dict]):
        beg = """\
            \\vspace{-1em}
            \\begin{center}
        """
        end = "\\end{center}\n"

        profiles_tex = []
        for prof in profiles:
            p = ProfileLink(**prof)
            profiles_tex.append(p.to_latex())

        final = dedent(beg) + indent("".join(profiles_tex), prefix="\t") + end
        return final

    def section_Experience(work: List[dict]):
        beg = """\
            \\section{Professional Experience}\n
            """

        mid = """\
            %
            \\vspace{1em}
            %
            """

        end = "\n"

        beg, mid = dedent(beg), dedent(mid)
        final = "" + beg

        for idx, work_entry in enumerate(work):
            w = Experience(**work_entry)
            final += w.to_latex()
            if idx != len(work) - 1:
                final += mid

        final += end
        return final

    def section_Education(education: List[dict]):
        beg = """\
            \\section{Education}\n
            """

        mid = """\
            %
            \\vspace{1em}
            %
            """

        end = "\n"

        beg, mid = dedent(beg), dedent(mid)
        final = "" + beg

        for idx, entry in enumerate(education):
            w = Education(**entry)
            final += w.to_latex()
            if idx != len(education) - 1:
                final += mid

        final += end
        return final

    def section_Projects(projects: List[dict]):
        beg = """\
            \\section{Projects}\n
            """

        mid = """\
            \\smallskip\n
            """

        end = "\n"

        beg, mid = dedent(beg), dedent(mid)
        final = "" + beg

        for idx, entry in enumerate(projects):
            w = Project(entry)
            final += w.to_latex()
            if idx != len(projects) - 1:
                final += mid

        final += end
        return final

    def section_TechnicalSkill(skills: List[dict]):
        beg = """\
            \\section{Technical Skills}
            \\begin{ListSkills}\n
            """

        end = """\
            \\end{ListSkills}
            """

        final = "" + dedent(beg)

        for entry in skills:
            ts = TechnicalSkill(**entry)
            final += "\t" + ts.to_latex()

        final += dedent(end)
        return final

    def section_Achievements(awards: List[dict]):
        beg = dedent(
            """\
            \\section{Achievements}
            
            \\begin{AchievementList}
        """
        )

        end = "\\end{AchievementList}"

        final = "" + beg
        for item in awards:
            a = Achievement(item)
            final += a.to_latex() + "\n"

        return final + end

    with open("./tmp/content.tex", "w") as content_file, open(
        "./tmp/meta.tex", "w"
    ) as meta_file:
        content = [
            section_ProfileLinks(data["basics"]["profiles"]),
            section_Experience(data["work"]),
            section_Education(data["education"]),
            section_TechnicalSkill(data["skills"]),
            section_Projects(data["projects"]),
            section_Achievements(data["awards"]),
        ]
        content_file.write("".join(content))
        meta_file.write(section_MetaData(data))


def main(logging_level: str = "warn"):

    logging.basicConfig(
        level=LOGGING_LEVEL_MAP[logging_level],
        filename="./resume_builder.log",
        filemode="a",
        format="%(levelname)s - %(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
    args = sys.argv
    if len(args) > 0:
        data = parse_json(Path(args[1]))
    else:
        data = parse_json()

    create_resume(data)


if __name__ == "__main__":
    main()
