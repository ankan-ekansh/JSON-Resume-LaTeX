import enum
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Tuple, Union
from pprint import pprint
import commentjson

import config
import resume.sections as sections


def create_resume_(data: dict, output_filename: str):
    class SECTIONS(enum.Enum):
        none = enum.auto()
        achv = enum.auto()
        skills = enum.auto()
        experience = enum.auto()
        education = enum.auto()
        project = enum.auto()

    section_mapping = {
        "experience": SECTIONS.experience,
        "education": SECTIONS.education,
        "technical_skill": SECTIONS.skills,
        "project": SECTIONS.project,
        "achievement": SECTIONS.achv,
    }

    def get_order(data: dict):
        default_order = ["experience", "education", "technical_skill", "project", "achievement"]

        if data.get("meta"):
            if data["meta"].get("order"):
                order = data["meta"].get("order")
                return [section_mapping.get(item, SECTIONS.none) for item in order]

        return [section_mapping.get(item, SECTIONS.none) for item in default_order]

    def create_metadata() -> str:
        nonlocal data
        meta_text = ""
        metadata = sections.MetaData(data["basics"])
        metadata.set_colors(data.get("meta"))
        meta_text += metadata.to_latex()

        profile_text = "\n"
        profiles = sections.ProfileLinks(data["basics"]["profiles"])
        profile_text += profiles.to_latex()

        return meta_text + profile_text

    def get_section_text(section_type: SECTIONS) -> str:
        """get text for all sections except meta and profile"""

        def get_section_name():
            nonlocal section_type
            mapping = {
                SECTIONS.achv: "Achievements",
                SECTIONS.skills: "Technical Skills",
                SECTIONS.experience: "Experience",
                SECTIONS.education: "Education",
                SECTIONS.project: "Projects",
            }
            return mapping[section_type]

        nonlocal data
        section_begin = "\\section{" + get_section_name() + "}\n"
        section_text = ""

        if section_type is SECTIONS.achv:
            section_text += sections.Achievements(data["awards"]).to_latex()

        if section_type is SECTIONS.skills:
            section_text += sections.TechnicalSkills(data["skills"]).to_latex()

        if section_type is SECTIONS.experience:
            section_text += sections.Experience(data["work"]).to_latex()

        if section_type is SECTIONS.education:
            section_text += sections.Education(data["education"]).to_latex()

        if section_type is SECTIONS.project:
            section_text += sections.Projects(data["projects"]).to_latex()

        return section_begin + section_text + "\n"

    order = get_order(data)
    meta_text = create_metadata()

    content_text = ""
    for section_type in order:
        content_text += get_section_text(section_type)

    logging.info(f"generated text, moving files to compilation")
    compile_tex_file(content_text, meta_text, output_filename)


def compile_tex_file(content_text: str, meta_text: str, output_filename: str) -> None:
    """compile tex file with main.tex string passed into input with temporary directory"""

    template_dir = config.TEMPLATE_DIR
    logging.info(f"using template {template_dir.name}")

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

        latemk_stdout = None
        error_raised = False
        try:
            move_process = run_process(
                f"""
                cp "{template_dir}/macros.tex" "{temp_path}/macros.tex"
                cp "{template_dir}/resume.tex" "{temp_path}/resume.tex"
                cp -R "./assets" "{temp_path}"
                mkdir -p out
                """
            )
            logging.info("moved files into temp directory")

            if config.KEEP_GENERATED_TEX:
                out_resume_path = f"{main_cwd}/out/resume"
                move_created_tex_files = run_process(
                    f"""
                    mkdir -p out/resume
                    cp "{template_dir}/macros.tex" "{out_resume_path}/macros.tex"
                    cp "{template_dir}/resume.tex" "{out_resume_path}/resume.tex"
                    cp "{temp_path}/content.tex" "{out_resume_path}/content.tex"
                    cp "{temp_path}/meta.tex" "{out_resume_path}/meta.tex"
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
                    latexmk -xelatex resume.tex
                    """,
                    timeout=config.LATEXMK_TIMEOUT,
                )

            except subprocess.TimeoutExpired as e:
                logging.error("Timeout during latexmk run:\n" + str(e))
                error_raised = True
                latemk_stdout = str(e.output.decode("utf-8"))

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
                logging.info(f"build and saved {output_filename}.pdf")

            finally:  # get latexmk log, in any case, evenif exceptions raised or not
                if config.KEEP_LOG_FILES:
                    try:
                        get_latex_log_process = run_process(
                            f"""
                            cd "{temp_path}"
                            cp -R "resume.log" "{main_cwd}/out/{output_filename}.log"
                            """
                        )

                        log_text = open(f"{main_cwd}/out/{output_filename}.log", "r").read()
                        if error_raised:
                            pprint("LaTeX Log\n" + log_text)

                    except subprocess.CalledProcessError as e:
                        logging.error(f"error during log_extraction process")

                    if latemk_stdout:
                        with open(f"{main_cwd}/out/latex_stdout.txt", "w") as stdout_file:
                            stdout_file.write(latemk_stdout)


def main():
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(levelname)s - %(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )

    def parse_json(path: Path = "./resume.jsonc") -> dict:
        with open(path, "r") as f:
            data = commentjson.load(f)
        return data

    args = sys.argv
    if len(args) - 1 == 2:
        data = parse_json(Path(args[1]))
        output_filename = args[2]

    elif len(args) - 1 == 1:
        data = parse_json(Path(args[1]))
        output_filename = args[1].split("/")[1].split(".")[0]

    create_resume_(data, output_filename)


if __name__ == "__main__":
    main()
