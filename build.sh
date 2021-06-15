#! /bin/bash

cp Resume/template/macros.tex tmp/macros.tex
cp Resume/template/resume.tex tmp/resume.tex
cd tmp
latexmk -xelatex -quiet resume.tex
mv -f resume.pdf ../Resume.pdf
latexmk -quiet -C
rm *.tex