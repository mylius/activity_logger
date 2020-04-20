from datetime import date
import json
import argparse
import configparser

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("act_log.ini")
    folder = config["Folder"]["folder"]

    parser = argparse.ArgumentParser(
        description="dict to return"
    )
    parser.add_argument(
        "dict",
        metavar="dict",
        type=str,
        help="Choose which Algorithms to run by passing arguments: bow - simple bag of words, bow_l - bag of words using lemmatisation, bow_ls - bag of words eliminating stopwords using lemmatisation and",
    )
    args = parser.parse_args()
    current_date = date.today()

    with open(folder+str(date.today())+".json") as f:
        data = json.load(f)
    total = data["total_time"]-data["other"]
    if args.dict not in data:
        print("error")
    else:
        if args.dict == "other":
            print((data[args.dict]/data["total_time"])*100)    
        else:
            print(data[args.dict]/total*100)
