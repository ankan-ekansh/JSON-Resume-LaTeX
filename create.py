import json
import os
import subprocess
import textwrap
from re import sub
from textwrap import dedent, indent
from typing import List

import commentjson
import pylatex
from rich import print
from rich.syntax import Syntax

from Resume.sections import (
    Achievements,
    Education,
    Experience,
    MetaData,
    ProfileLink,
    Project,
    TechnicalSkills,
)


def print_latex_syntax(code: str):
    syn = Syntax(code, lexer_name="latex", background_color="default")
    print(syn, end="")


def print_json(data: dict):
    syn = Syntax(
        code=json.dumps(data, indent=2), lexer_name="json", background_color="default"
    )
    print(syn)
    print("\n")


def parse_json() -> dict:
    with open("./resume.jsonc", "r") as f:
        d = commentjson.load(f)
    return d


def create_resume_content(data: dict):
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

    def section_TechnicalSkills(skills: List[dict]):
        beg = """\
            \\section{Technical Skills}
            \\begin{ListSkills}\n
            """

        end = """\
            \\end{ListSkills}
            """

        final = "" + dedent(beg)

        for entry in skills:
            ts = TechnicalSkills(**entry)
            final += "\t" + ts.to_latex()

        final += dedent(end)
        return final

    with open("./tmp/content.tex", "w") as f:
        content = [
            section_ProfileLinks(data["basics"]["profiles"]),
            section_Experience(data["work"]),
            section_Education(data["education"]),
            section_TechnicalSkills(data["skills"]),
            section_Projects(data["projects"]),
        ]
        f.write("".join(content))

    with open("./tmp/meta.tex", "w") as f:
        f.write(section_MetaData(data))

    def build_resume():
        p = subprocess.run(
            """\
                cp Resume/template/macros.tex tmp/macros.tex
                cp Resume/template/resume.tex tmp/resume.tex
                cd tmp
                latexmk -xelatex -quiet resume.tex
                mv -f resume.pdf ../Resume.pdf
                latexmk -quiet -C
                rm *.tex
                """,
            shell=True,
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            print(f"[red]{p.stderr}")

    build_resume()


def main():
    data = parse_json()
    create_resume_content(data)


if __name__ == "__main__":
    main()
