# parser-analysis

Some experiments in a more fine-grained approach to analyzing the output of dependency parsers.

[`constructions.py`](constructions/constructions.py) defines a set of (hopefully) language-independent constructions and a UDApi block for marking them in CoNNL-U files. [`eval.py`](eval.py) then calculates per-construction UAS and LAS based on those markings.
