init: init-pip init-font

init-pip:
	pip install -r requirements.txt

# Get required fonts
fontfile=BebasNeue-Regular.ttf
font_dir=resources
fontzip=bebas_neue.zip

init-font: $(font_dir)/$(fontfile)
$(font_dir)/$(fontfile):
	wget https://dl.dafont.com/dl/?f=bebas_neue -O "$(fontzip)"
	unzip -j -o "$(fontzip)" "$(fontfile)" -d "$(font_dir)"
	rm $(fontzip)

test:
	PYTHONPATH="$(shell pwd)" pytest

flake8:
	# Ignore: E501 (too long lines)
	flake8 src *.py --ignore E501

.PHONY: init init-font init-pip test flake8
