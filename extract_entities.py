# import libraries
import os, sys
import pandas as pd
import numpy as np

import subprocess
import argparse
import functions
import glob

from ast import literal_eval
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_fscore_support

from pathlib import Path


#--------------- PART NECESSARY TO MAKE UTH-BERT WORK ------------
os.environ['TF_KERAS'] = '1'
os.environ['MECABRC'] = "/etc/mecabrc" # 環境変数でmecabrcの場所を指定
sys.path.append('./uth-bert')

pretrained_model_dir_path = 'UTH_BERT_BASE_512_MC_BPE_WWM_V25000_352K' 
pretrained_bert_config_file_path = os.path.join(pretrained_model_dir_path, 'config.json') 
pretrained_model_checkpoint_path = os.path.join(pretrained_model_dir_path, 'model.ckpt-352000.data-00000-of-00001')
pretrained_vocab_file_path = os.path.join(pretrained_model_dir_path, 'vocab.txt') 

manbyo_dic_path = './MANBYO_201907_Dic-utf8.dic'

cmd = 'echo `mecab-config --dicdir`"/mecab-ipadic-neologd"'
neologd_dic_dir_path = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()

from preprocess_text import preprocess as my_preprocess
from tokenization_mod import MecabTokenizer, FullTokenizerForMecab

#------------------ READING FILES --------------------------------
form_mode_route_lists = pd.read_excel("./data/in/form_mode_route_list.xlsx", engine='openpyxl')
drugs = pd.read_csv('./data/in/drugs.csv',
        converters={
            'tokenized': literal_eval
        })

#------------------ PREPROCESSING DATA ---------------------------
form_list = form_mode_route_lists['form_list'].values.tolist()
form_list.pop(-1) #erase nan value in list

mode_list = [m for m in form_mode_route_lists['mode_list'].values.tolist() if not pd.isnull(m)]
route_list = [r for r in form_mode_route_lists['route_list'].values.tolist() if not pd.isnull(r)]

drug_list = drugs['pure_drug_name'].values.tolist()

# UTH-BERT Tokenization model from https://github.com/jinseikenai/uth-bert

if __name__ == '__main__':

    #Special token for a Person's name (Do not change)
    name_token = "＠＠Ｎ"

    #Path to the mecab-ipadic-neologd
    mecab_ipadic_neologd = neologd_dic_dir_path

    #Path to the J-Medic (We used MANBYO_201907_Dic-utf8.dic)
    mecab_J_medic = manbyo_dic_path

    #Path to the uth-bert vocabulary
    vocab_file = pretrained_vocab_file_path

    #MecabTokenizer
    sub_tokenizer = MecabTokenizer(mecab_ipadic_neologd=mecab_ipadic_neologd,
                                   mecab_J_medic=mecab_J_medic,
                                   name_token=name_token)

    #FullTokenizerForMecab
    tokenizer = FullTokenizerForMecab(sub_tokenizer=sub_tokenizer,
                                      vocab_file=vocab_file,
                                      do_lower_case=False)

    #Argument parser
    parser = argparse.ArgumentParser(description='Parser for Japanese Medical Incident Reports.\nParse words into 12 different entity categories. More information about these entity categories can be found in this paper : "https://aclanthology.org/2020.lrec-1.563.pdf"')
    parser.add_argument("-r", "--report", type=str, help="The report to be parsed.")
    parser.add_argument("-f", "--file",  type=str, help="The path of the file containing the report to be parsed.")
    parser.add_argument("-x", "--excel", type=str, help="The path of a Excel file (.xslx) containing several reports.\nMust contain a column named 'reports' and a id column unnamed.")
    parser.add_argument("-f1", "--f1score", type=str, help="The path of a Excel file (.xslx) containing several reports.\nMust contain a column named 'reports' and a id column unnamed.")
    parser.add_argument("-o", "--output", type=str, help="The path to the output file results will be written into. If the input file is an Excel file, the output should have .xlsx as extension.")

    #args = parser.parse_args()
    args, unknown = parser.parse_known_args()

    if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
        parser.print_help()
        sys.exit(1)
    elif (args.report and args.file) or (args.report and args.excel) or (args.file and args.excel) or (args.report and args.file and args.excel):
            print("You can pass only one input at a time.")
            sys.exit(1)

    elif args.excel:
        # insert input file as dataframe  
        df = pd.read_excel(args.excel,  engine='openpyxl')
        file_name = args.excel.replace(".xlsx", "")

        #preprocessing incident reports
        df["reports"] = df["reports"].apply(lambda x: my_preprocess(x))
        reports_df = df.drop_duplicates(subset=['reports'], keep='first')
        
        # Find all entities in every report rows by using entity searching rule base functions
        reports_df['entities'] = reports_df.apply(lambda x: functions.find_entities((x['reports']), 
                                tokenizer.tokenize(x['reports']),
                                drug_list, form_list, mode_list, route_list), axis=1)

        reports_df['entities'] = reports_df.apply(lambda x: functions.find_entities((x['reports']), 
                                    tokenizer.tokenize(x['reports']),
                                    drug_list, form_list, mode_list, route_list), axis=1)
                                    
        #Create new dataframe then insert all predicted results
        entities_df = pd.DataFrame(columns=['id', 'entity_type', 'entity_name', 'start_idx', 'end_idx','reports'])    
        for idx, report in reports_df.iterrows():
            for entity in report['entities']:
                new_row = pd.Series([report['id'], entity[1], entity[0], entity[2], entity[3], report["reports"]], index=entities_df.columns)
                entities_df = pd.concat([entities_df, new_row.to_frame().T], ignore_index=True)
                
        print("Predicted result shape: ", entities_df.shape)
        entities_df = entities_df.drop_duplicates()
        print("Predicted result shape after duplicates: ", entities_df.shape)
        entities_df =functions.duplicate_filter(entities_df)
        
        if not args.output:
            args.output = "./data/out/rulebase_extracted_results.xlsx"

        print("Saving results in " + args.output)
        entities_df.to_excel(args.output)

    elif args.f1score:
        # insert input file as dataframe  
        df = pd.read_excel(args.f1score,  engine='openpyxl')

        #preprocessing incident reports
        df["reports"] = df["reports"].apply(lambda x: my_preprocess(x))
        reports_df = df.drop_duplicates(subset=['reports'], keep='first')
        
        # Find all entities in every report rows by using entity searching rule base functions
        reports_df['entities'] = reports_df.apply(lambda x: functions.find_entities((x['reports']), 
                                tokenizer.tokenize(x['reports']),
                                drug_list, form_list, mode_list, route_list), axis=1)

        reports_df['entities'] = reports_df.apply(lambda x: functions.find_entities((x['reports']), 
                                    tokenizer.tokenize(x['reports']),
                                    drug_list, form_list, mode_list, route_list), axis=1)
                                    
        #Create new dataframe then insert all predicted results
        entities_df = pd.DataFrame(columns=['id', 'entity_type', 'entity_name', 'start_idx', 'end_idx','reports'])    
        for idx, report in reports_df.iterrows():
            for entity in report['entities']:
                new_row = pd.Series([report['id'], entity[1], entity[0], entity[2], entity[3], report["reports"]], index=entities_df.columns)
                entities_df = pd.concat([entities_df, new_row.to_frame().T], ignore_index=True)
                
        print("Predicted result shape: ", entities_df.shape)
        entities_df = entities_df.drop_duplicates()
        print("Predicted result shape after duplicates: ", entities_df.shape)
        entities_df =functions.duplicate_filter(entities_df)

        #erase and rename columns from actual dataframe to match predicted results
        df.rename(columns={"entity": "entity_type"}, inplace=True)
        df_actual = df[['id', 'entity_type', 'entity_name', 'start_idx', 'end_idx','reports']]
        entity_list = ["Date", "Dosage", "Drug","Duration","Form_form","Form_mode","Frequency","Route","Strength_amount","Strength_concentration","Strength_rate","Timing"]

        df_actual = df_actual.loc[df_actual.apply(lambda x: x.entity_type in entity_list, axis=1)]

        print("Actual result shape: ", df_actual.shape)
        df_actual = df_actual.drop_duplicates()
        print("Actual result shape after duplicates: ", df_actual.shape)

        #calculate True positive, False positive, False negative answers from predicted, actual dataframe 
        df_total = functions.calc_confusion_metrics(entities_df, df_actual)
        print("Total result shape: ", df_total.shape)
    
        df_total["predicted"]= df_total["predicted"].astype(int)
        df_total["actual"]= df_total["actual"].astype(int)

        #calculate precision, recall, f1_score on all 11 entities
        df_result = pd.DataFrame(columns=['Entity_type', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F1_score']) #create final result dataframe
        
        entities = df_total.entity_type.unique()

        precision, recall, f1, a = precision_recall_fscore_support(df_total['actual'], df_total['predicted'], average='binary')
        tn, fp, fn, tp = confusion_matrix(df_total['actual'], df_total['predicted']).ravel()
        print(f"tp: {tp}, fp: {fp}, fn: {fn}, precision: {round(precision,2)}, recall: {round(recall,2)}, fl score: {round(f1,2)}")

        # calculating confution matrix by each entity
        for ent in entities:
            df_sub = df_total[df_total.entity_type == ent]
                    
            tn, fp, fn, tp = confusion_matrix(df_sub['actual'], df_sub['predicted']).ravel()

            precision, recall, f1, a = precision_recall_fscore_support(df_sub['actual'], df_sub['predicted'], average='binary')
            new_row = (ent, tp, fp, fn, round(precision,2), round(recall,2), round(f1,2))

            df_result.loc[df_result.shape[0]] = new_row
        
        if not args.output:
            args.output = "./data/out/rulebase_extracted_results.xlsx"

        print("Saving results in " + args.output)
        df_total.to_excel(args.output)
        df_result.to_excel("./data/out/all_entity_f1_score_results.xlsx")

    else:
        if args.report:
            data = args.report            
        else:
            with open(args.file, 'r') as f:
                data = f.read()

        tokenized_report = tokenizer.tokenize(data)
        #Calling the function that find the entities
        all_entities = functions.find_entities(data, tokenized_report, drug_list, form_list, mode_list, route_list)
        print("Results of parsing for : {}".format(data) + '\n' + str(all_entities))
        
        if not args.output:
            args.output = "./data/out/result.txt"
        with open(args.output, "a") as f:
            print("Saving results in " + args.output)
            f.write("Results of parsing for : {}".format(data) + '\n')
            f.write(str(all_entities)+'\n')