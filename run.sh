#!/bin/bash

docker_run() {
    docker run -it --rm \
    --name json-resume-create \
    -v "$(pwd):/home/app/" -w "/home/app/" danteev/texlive:latest \
    bash ./run.sh run_build
}

run_build() {
    adduser --quiet --disabled-password --gecos "" nonroot
    pip3 install -q -r script/requirements.txt
    python3 script/create.py "./resume.jsonc" "resume_IshaanAditya"
    chown -R nonroot: "out/"
}

# "$@" is used to expand command line calls to function names
# htt
$@