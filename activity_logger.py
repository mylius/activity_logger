import os
import subprocess
import re
import time
import atexit
from datetime import date
import sys, signal
import json
import configparser


def signal_handler(signal, frame):
    logger.save(date.today())
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class category:
    """
    A category of windows, to be identified by their title.
    Parameters:
    keywords(list): A list of strings. Give a list of keywords, that appear in the title of the windows you want to identify.
    name(string): A string that identifies this category.
    """

    def __init__(self, name, keywords):
        self.name = name
        self.time = 0
        self.keywords = keywords
        self.time = 0

    def __repr__(self):
        return self.keywords


def load_conf():
    config = configparser.ConfigParser()
    config.read("act_log.ini")
    folder = config["Folder"]["folder"]
    idle_time = int(config["magic numbers"]["idle_time"])*1000
    write_frequency = int(config["magic numbers"]["write_frequency"])*1000
    categories = {}
    for item in config["Categories"]:
        categories[item] = category(item, config["Categories"][item].split(","))
    categories["other"] = category("other", [])
    return categories, folder, idle_time, write_frequency


def get_active_window_title():
    """
    Uses xprop to get the current window name.
    Returns the name.

    Probably taken from here: https://askubuntu.com/questions/1199306/python-get-foreground-application-name-in-ubuntu-19-10
    """
    root = subprocess.Popen(
        ["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE
    )
    stdout, stderr = root.communicate()

    m = re.search(b"^_NET_ACTIVE_WINDOW.* ([\w]+)$", stdout)
    if m != None:
        window_id = m.group(1)
        window = subprocess.Popen(
            ["xprop", "-id", window_id, "WM_NAME"], stdout=subprocess.PIPE
        )
        stdout, stderr = window.communicate()
    else:
        return None

    match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
    if match != None:
        return match.group("name").strip(b'"')

    return None


categories, folder, idle_time, write_frequency = load_conf()


class activity_recorder:
    """
    This class identifies the current window, categorizes it, and archives the recorded usage.
    It also has a method for exporting a conky file.
    """

    def __init__(self):
        self.current_category = categories["other"]
        self.path = os.path.expanduser(folder)
        print(self.path)
        self.start_time = time.time()
        self.current_date = date.today()
        self.total_time = 0
        self.idle = False
        self.update = False

    def __reset__(self):
        for cat in categories:
            cat.time = 0
        self.total_time = 0

    def count_time(self):
        if int(subprocess.check_output("xprintidle")) > idle_time and not self.idle:
            print("Start idling")
            self.idle = True
            self.idle_time = time.time()
        if int(subprocess.check_output("xprintidle")) <= idle_time and self.idle:
            print("Stop idling")
            self.idle = False
            self.idle_time = time.time() - self.idle_time
            self.update = True
            print(self.idle_time)
        if date.today() != self.current_date:
            self.save(self.current_date)
            self.current_date = date.today()
        window_name = str(get_active_window_title()).lower()
        found = False
        for item in self.current_category.keywords:
            if item in window_name:
                found = True
        if not found:
            if self.update:
                self.current_category.time += (
                    time.time() - self.start_time - self.idle_time
                )
                self.total_time += time.time() - self.start_time - self.idle_time
                self.update = False
            else:
                self.current_category.time += time.time() - self.start_time
                self.total_time += time.time() - self.start_time
            self.start_time = time.time()
            found_cat = False
            for cat in categories.values():
                for keyword in cat.keywords:
                    if keyword in window_name:
                        found_cat = True
                        self.current_category = cat
                print(cat.name, cat.time)
            if not found_cat:
                self.current_category = categories["other"]
            print(self.total_time)
            print("_________________________")

    def load(self, filename):
        filename = str(filename)
        print("loading...")
        if os.path.exists(self.path + filename + ".json"):
            with open(self.path + filename + ".json") as f:
                data = json.load(f)
                for key, value in data.items():
                    for cat in categories.values():
                        if cat.name == key:
                            cat.time = value
                    if key == "total_time":
                        self.total_time = value

    def save(self, filename):
        filename = str(filename)
        print("Saving...")
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        data = {}
        for cat in categories.values():
            data[cat.name] = cat.time
        data["total_time"] = self.total_time
        with open(self.path + filename + ".json", "w") as f:
            json.dump(data, f, indent=2)


class GracefulKiller:
    """
    If this.kill_now is True the script is killed gracefully, by executing additional functions before terminating.

    Taken from: https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
    """

    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


if __name__ == "__main__":
    logger = activity_recorder()
    logger.load(date.today())
    i = 0
    killer = GracefulKiller()
    while not killer.kill_now:
        logger.count_time()
        i += 1
        if i % write_frequency == 0:
            logger.save(date.today())
    logger.save(date.today())
