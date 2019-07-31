# Pandoc_tex_nos 
This is a set of pandoc filters to number tables, figures, and equations from latex to word documents. It only works for that specific case. These filters are built upon pandoc-eq-nos v 1.4.3 [https://github.com/tomduck/pandoc-eqnos](https://github.com/tomduck/pandoc-eqnos) 

I haven't tested these filters thoroughly, so use it at your own risk
# Requirements
You first need to install the following python modules:
	- `pip install pandocfilters pandoc-xnos`
# Known issues:

    - The labels in tables and figures should be included inside the caption in the .tex file, e.g., `\caption{\label{tableA}This is table A}`


