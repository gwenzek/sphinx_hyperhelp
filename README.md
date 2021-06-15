# Sphinx Hyperhelp

[Sphinx](https://www.sphinx-doc.org/en/master/index.html) builder that outputs 
[HyperHelp](https://github.com/STealthy-and-haSTy/hyperhelpcore) files.
HyperHelp files are destined to be read inside [Sublime Text](https://www.sublimetext.com/)
The goal of this project is to be able to read in Sublime Text
the documentation of all projects using Sphinx.
Notably [Python](https://docs.python.org/3/) documentation.

## License

This plugin is released under the [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause).

This plugin is mostly based on the builtin [Sphinx text builder](https://www.sphinx-doc.org/en/master/usage/builders/index.html?highlight=text%20builder#sphinx.builders.text.TextBuilder).

Some of the code is only a slight modification of Sphinx.
[Sphinx license](./LICENSE#17)


## Get started

...

## How-to ?

...

## Architecture

This plugin is mostly based on the builtin [Sphinx text builder](https://www.sphinx-doc.org/en/master/usage/builders/index.html?highlight=text%20builder#sphinx.builders.text.TextBuilder).
There are some visual differences so that the generated text looks
nice when parsed by HyperHelp renderer.
But a big part of the work is also to generate the HyperHelp index,
that registers all anchors.

`hyperhelp.py` files contains helpers to build the index.
`help_writer.py` is doing the core of the work,
and is implemented by only overriding
some of the TextTranslator methods.

`tests` 

## Reference

...

## Todo list

* fix broken links (currently 176 unresolved topics)
* ensure links are surrounded by spaces
* incremental compilation 

## Crazy ideas

* Use unicode to render maths: "E = mc^2" -> "E = mc²"
* images using phantoms ? this should be an HyperHelp feature
