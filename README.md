# Parser for Medical Incident Reports

This folder contains a script that allows it's users to parse a Medical Incident Reports (MIR) into 12
different category of entities. These entities can be found in [this paper](https://aclanthology.org/2020.lrec-1.563.pdf).

## Files

In the `python` folder, you should have the following files :

    - `extract_entities.py` which is the script itself.
    - `functions.py` which contains the functions used by the parser.
    - `./data/in/form_mode_route_list.xlsx` Excel file containing the different form, mode and route possible entities.
    - `./data/in/drugs.csv` containing possible drugs in a tokenized format.
    - `./data/in/hiyari_medical_accidents.xlsx` containing all year hiyari medical accidents.
    - `./data/in/medical_accidents.xlsx` containing all year medical accident reports.
    - `./data/in/test_50.xlsx` The Input file containing 50 reports that we annotated manually for testing the script. (You can use your own input reports instead of this one.)
    - `./data/out/all_entity_f1_score_results.xlsx` The Output file containing entity specific scores.
    - `./data/out/rulebase_extracted_results.xlsx` The Output file containing extraction result.

UTH-BERT model itself.

The `uth-bert` folder contains uth-bert files that can be found at [this GitHub repository](https://github.com/jinseikenai/uth-bert)

## Downloads and installations

### Dependencies
To make the parser work, you'll need to download some files and install some dependencies. All of these steps can be found in [this website](https://qiita.com/Kunikata/items/d9fda2351a273a7412f6)
Be careful, The pretrained UTH-BERT model on the Qiita website is deprecated ! Download the new one by typing this command : `https://ai-health.m.u-tokyo.ac.jp/labweb/dl/uth_bert/UTH_BERT_BASE_512_MC_BPE_WWM_V25000_352K.zip`

#### Dependency error handling
For MacOSX, in some case mecabrc file doesn't install properly when installing mecab-python3 package. In that case, install unidic complete version by running following command: 
- `python -m unidic download`
Also when following mecab-ipadic-neologd dictionary related error occurs:
> [ifs] no such file or directory: /usr/local/lib/mecab/dic/mecab-ipadic-neologd/*
you might need to reinstall **mecab-ipadic-neologd** again by: 
1. First delete /mecab folder
    - `rm -rf  /usr/local/lib/mecab`
2. Then reunstall "mecab-ipadic-NEologd". All of these steps can be found in [this website](https://github.com/neologd/mecab-ipadic-neologd)

### Installation
1. Install python version => 3.8.0:
   - `brew install pyenv`
   - `pyenv install 3.8.0`
1. Create and activate with dependencies:
   - `pip install virtualenv`
   - `virtualenv --python=python3.8.0 envname`
   - `source envname/bin/activate`
2. Install necessary python library dependencies:
   - `pip install -r requirements.txt`

## How to use the script ?

The script (`extract_entities.py`) has several options that you can use to pass some arguments.

    - `-h` or `--help` displays a help message.
    - `-r` or `--report` tells the parser that the following string is the report to be parsed
    - `-f` or `--file` allows to pass the report in a file. It should be use with the path of the file where the report is contained.
    - `-x` or `--excel` Input should be an Excel file (.xslx) that contains reports in a column named `reports`. It should also contain a nameless column representing indexes of entities.
    - `-f1` or `--f1score` For calculating f1 score for each entities.Input should be an Excel file (.xslx) that contains reports in a column named `reports`. It should also contain a nameless column representing indexes of entities.
    - `-o` or `--output` Path of the file where the results of the parsing will be saved. If -x is used, the output path should contain the .xlsx extension. In both cases if not precised, results
    will be saved in a file accorded to which option is used.

Usage examples :

    - `python3 extract_entities.py -x ./data/in/test_50.xlsx -o ./data/out/test_50_results.xlsx`
    - `python3 extract_entities.py -f1 ./data/in/test_50.xlsx -o ./data/out/test_50_results.xlsx`
    - `python3 extract_entities.py -r 10月19日、朝の清拭時に前胸部に2枚 貼ってあったはずのフェンタニルクエン酸塩2mgテープが1枚のみ貼られていることに気が付く。前日の日勤担当者は確かに前胸部に2枚貼っていたが清拭時に1枚のみであった。`
