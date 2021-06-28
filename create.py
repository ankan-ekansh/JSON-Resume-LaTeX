import sys
import json
import logging
import os
import subprocess
import textwrap
from re import sub, template
from textwrap import dedent, indent
from typing import Iterable, List, Tuple

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


def create_resume(data: dict,):
    """
    High Level Function to create Resume .tex and .pdf files from the `json` resume spec passed in. Uses helper functions and submodule classes for actual building of resume tex file

    Args:
        data (dict): [description]
    """
    templates_path = Path("./Resume/template.json")

    def get_template(key: str, file: Path) -> Tuple[str]:
        with open(file, "r") as f:
            data: dict = json.load(f)

        def join(x: Iterable[str]):
            return "" if x[0] is None else "\n".join(x)

        if data.get(key):
            vals = data.get(key)
            begin, mid, end = map(
                join, (vals.get("begin"), vals.get("mid"), vals.get("end"))
            )
            return (begin, mid, end)

        else:
            return (None, None, None)

    def section_MetaData(data: dict):
        m = MetaData(data["basics"])
        m.set_colors(data["meta"])
        return m.to_latex()

    def section_ProfileLinks(profiles: List[dict]):
        beg, mid, end = get_template("ProfileLink", templates_path)
        profiles_tex = []
        for prof in profiles:
            p = ProfileLink(**prof)
            profiles_tex.append(p.to_latex())

        final = dedent(beg) + indent("".join(profiles_tex), prefix="\t") + end
        return final

    def section_Experience(work: List[dict]):
        beg, mid, end = get_template("Experience", templates_path)
        final = "" + beg

        for idx, work_entry in enumerate(work):
            w = Experience(**work_entry)
            final += w.to_latex()
            if idx != len(work) - 1:
                final += mid

        return final + end

    def section_Education(education: List[dict]):
        beg, mid, end = get_template("Education", templates_path)
        final = "" + beg

        for idx, entry in enumerate(education):
            w = Education(**entry)
            final += w.to_latex()
            if idx != len(education) - 1:
                final += mid

        return final + end

    def section_Projects(projects: List[dict]):
        beg, mid, end = get_template("Project", templates_path)
        final = "" + beg

        for idx, entry in enumerate(projects):
            w = Project(entry)
            final += w.to_latex()
            if idx != len(projects) - 1:
                final += mid

        return final + end

    def section_TechnicalSkill(skills: List[dict]):
        beg, mid, end = get_template("TechnicalSkill", templates_path)
        final = "" + beg

        for entry in skills:
            ts = TechnicalSkill(**entry)
            final += "\t" + ts.to_latex()

        return final + end

    def section_Achievements(awards: List[dict]):
        beg, mid, end = get_template("Achievement", templates_path)
        final = "" + beg
        for item in awards:
            a = Achievement(item)
            final += a.to_latex() + "\n"

        return final + end

    def get_order(data: dict) -> List[str]:
        if data.get('meta'):
            if data['meta'].get('order'):
                return data['meta'].get('order')
        return None
    
    sections_mapping = {
        "experience": section_Experience(data["work"]),
        "education": section_Education(data["education"]),
        "technical_skill": section_TechnicalSkill(data["skills"]),
        "project": section_Projects(data["projects"]),
        "achievement": section_Achievements(data["awards"]),
    }

    with open("./tmp/content.tex", "w") as content_file, open(
        "./tmp/meta.tex", "w"
    ) as meta_file:

        order = get_order(data)
        content = [section_ProfileLinks(data["basics"]["profiles"])]
        content += [sections_mapping[k] for k in order]

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
