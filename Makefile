default: run

run:
	python3 taskmanager.py


doc: readme.html
	xdg-open readme.html

readme.html: readme.md
	markdown readme.md > readme.html
