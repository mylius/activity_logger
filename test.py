import configparser

config = configparser.ConfigParser()
config.read("act_log.ini")
folder = config["Folder"]["folder"]
categories = {}
for item in config["Categories"]:
    categories[item] = config["Categories"][item].split(",")
for item in categories.values():
    print(item)