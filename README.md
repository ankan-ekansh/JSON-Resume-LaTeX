# `JSON-Resume` to `LaTeX`

A python parser to create `LaTeX` PDFs from `JSON-Resume` spec (+ few useful modifications in the spec)

All the definitions of how each object in the `resume.jsonc` are given in the `macros.tex` file. Contents are parsed accoring to the defintion of the macros and used with a main file which includes all the required dependencies in `LaTeX` environment.

The build process uses dockerized TexLive ([`danteev/texlive`](https://hub.docker.com/r/danteev/texlive/)) which is the most complete containerized texlive instance and can be used with GitHub Actions and other CI/CD tools along with compilation in servers wherein it can be pulled from DockerHub.

The docker image can be called to build a PDF version of the resume using

```shell
bash build.sh docker_build
```

The above command can be used with the root as `pwd` and a `Resume.pdf` can be found in the root directory once the execution is over. `docker` must be installed.
