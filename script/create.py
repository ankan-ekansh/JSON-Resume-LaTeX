import os
import sys
import json
import config
import pylatex
import logging
import tempfile
import subprocess
import commentjson

from pathlib import Path
from textwrap import dedent, indent
from typing import Iterable, List, Tuple

from resume.sections import (
    MetaData,
    Achievement,
    Education,
    Experience,
    ProfileLink,
    Project,
    TechnicalSkill,
)


def parse_json(path: Path = "./resume.jsonc") -> dict:
    with open(path, "r") as f:
        d = commentjson.load(f)
    return d


def create_resume(data: dict, output_filename: str):
    """
    High Level Function to create Resume from the `json` resume spec passed in. Uses helper functions and submodule classes for actual building of resume tex file

    Args:
        data (dict): [description]
    """
    templates_path = Path("./script/resume/template.json")

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

    def get_order(data: dict) -> List[str]:
        if data.get("meta"):
            if data["meta"].get("order"):
                return data["meta"].get("order")
        return None

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

    sections_mapping = {
        "experience": section_Experience(data["work"]),
        "education": section_Education(data["education"]),
        "technical_skill": section_TechnicalSkill(data["skills"]),
        "project": section_Projects(data["projects"]),
        "achievement": section_Achievements(data["awards"]),
    }

    meta_file_text = section_MetaData(data)
    order = get_order(data)
    content = [section_ProfileLinks(data["basics"]["profiles"])]
    content += [sections_mapping[k] for k in order]
    content_file_text = "".join(content)

    compile_tex_file(content_file_text, meta_file_text, output_filename)


def compile_tex_file(content_text: str, meta_text: str, output_filename: str) -> None:
    """compile tex file with main.tex string passed into input with temporary directory"""

    with tempfile.TemporaryDirectory() as td:
        temp_path = Path(td)
        main_cwd = Path(os.getcwd())
        outdir_nm = output_filename

        with open(temp_path.joinpath("content.tex"), "w") as content_file:
            content_file.write(content_text)

        with open(temp_path.joinpath("meta.tex"), "w") as meta_file:
            meta_file.write(meta_text)

        def run_process(cmd: str, timeout=config.TIMEOUT):
            process = subprocess.run(
                cmd,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
            )
            return process

        error_raised = False
        try:
            move_process = run_process(
                f"""
                cp "./script/resume/template/macros.tex" "{temp_path}/macros.tex"
                cp "./script/resume/template/resume.tex" "{temp_path}/resume.tex"
                cp -R "./assets" "{temp_path}"
                mkdir -p out
                """
            )

        except subprocess.TimeoutExpired as e:
            logging.error(f"Timeout during initial move\n" + str(e))

        except subprocess.CalledProcessError as e:
            logging.error(f"ProcessError for initial move:\n" + str(e))

        else:
            # no exception generated in move block, can move to compilation phase
            try:
                latexmk_process = run_process(
                    f"""
                    cd "{temp_path}"
                    latexmk -xelatex -quiet resume.tex
                    """,
                    timeout=config.LATEXMK_TIMEOUT,
                )

            except subprocess.TimeoutExpired as e:
                logging.error("Timeout during latexmk run:\n" + str(e))
                error_raised = True

            except subprocess.CalledProcessError as e:
                logging.error("ProcessError for latexmk:\n" + str(e))
                error_raised = True
                
            else:  # get pdf file, as no exceptions raised
                get_pdf_file_proc = run_process(
                    f"""
                    cd "{temp_path}"
                    cp -R "resume.pdf" "{main_cwd}/out/{output_filename}.pdf"
                    """
                )

            finally:  # get latexmk log, in any case, evenif exceptions raised or not
                get_latex_log_process = run_process(
                    f"""
                   cd "{temp_path}"
                    cp -R "resume.log" "{main_cwd}/out/{output_filename}.log"
                    """
                )
                log_text = open(f"{main_cwd}/out/{output_filename}.log", "r").read()
                if error_raised:
                    print("LaTeX Log\n" + log_text)


def main():
    logging.basicConfig(
        level=logging.WARN,
        format="%(levelname)s - %(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )

    args = sys.argv
    if len(args) - 1 == 2:
        data = parse_json(Path(args[1]))
        output_filename = args[2]

    elif len(args) - 1 == 1:
        data = parse_json(Path(args[1]))
        output_filename = args[1].split("/")[1].split(".")[0]

    create_resume(data, output_filename)


if __name__ == "__main__":
    main()
