#! /bin/bash

function clean_tmp() {
    cd "tmp"
    latexmk -quiet -C
    rm *.tex
    cd ..
}

function move_files() {
    cp "./Resume/template/macros.tex" "./tmp/macros.tex"
    cp "./Resume/template/resume.tex" "./tmp/resume.tex"
}

function build_local_texlive() {
    cd "tmp"
    latexmk -xelatex -quiet resume.tex
    mv -f "resume.pdf" "../Resume.pdf"
    cd ..
}

function docker_build() {
    docker run -it --rm \
        --name resume-latex-build \
        -v "$(pwd):/home/resume_build/" -w "/home/resume_build/" danteev/texlive:latest \
        bash ./build.sh run_build
}

function run_build() {
    pip3 install -q -r requirements.txt
    python3 create.py "./resume.jsonc"
    move_files
    build_local_texlive
    clean_tmp
}

# "$@" is used to expand command line calls to funcion names
# https://stackoverflow.com/a/16159057/13196816
"$@"