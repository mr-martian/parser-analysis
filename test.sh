#!/bin/bash

cat test.gold.conllu | PYTHONPATH=".:$PYTHONPATH" udapy -qs .constructions.Constructions > test.gold-mark.conllu 
python3 eval.py test.gold-mark.conllu test.system.conllu
