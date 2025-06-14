import pandas as pd
import sqlite3
from collections import Counter

class TitleTree:
    def __init__(self, value, name_list = None):
        self.value = value
        self.titles = []
        self.children = {}
        self.depth = 0 #Initial height
        self.fullname = ""
        if name_list:
            for title in name_list:
                self.add_child(title)


    def add_child(self, new):
        words = new.split()
        if len(words) == self.depth or (self.depth + 1 == len(words) and words[self.depth].isnumeric()):
            self.titles.append(new)
            return
        word = new.split()[self.depth].replace(":","").replace(",","").replace("/","").replace("-","")
        if word not in self.children:
            new_tree = TitleTree(word)
            self.children[word] = new_tree
            new_tree.depth = self.depth + 1
            new_tree.fullname = (self.fullname+" "+ word).strip()

        new_tree = self.children[word]
        new_tree.add_child(new)

    def get_prefixes(self):
        return ["the", "a", "an", "of", "and", "in", "on", "for", "with", "edition", "remastered", "definitive",
                "deluxe", "ultimate", "complete", "gold", "anniversary", "hd", "goty", "director's", "cut", "game",
                "season", "chapter", "volume", "episode", "beta", "alpha", "demo", "vr"]

    def search(self, title):
        """ Searches for existing titles only.
            retrieves the last relevant franchise name"""
        words = title.split()
        found = False
        for child in self.children.keys():
            if words[0] == child:
                found = True
        if not found:
            return title,[title]
        tree = self.children[words[0].replace(":","").replace(",","").replace("/","").replace("-","")]
        prev = tree
        last_count = tree.all_titles()
        if title.startswith("Dead"):
            pass
        for i in range(5):
            if i + 1 == len(words) or words[i+1].isnumeric():
                for j in last_count:
                    if i <= 3 and len(j) > 5:
                        return tree.fullname, [title]
                return prev.fullname,last_count
            new_count = tree.all_titles()
            if len(words) > 3 and i > 1 and len(last_count) > len(new_count) and words[tree.depth] not in tree.get_prefixes():
                if words[0] == prev.fullname:
                    return tree.fullname, last_count
                return prev.fullname,last_count
            last_count = new_count
            if tree.value.lower() not in tree.get_prefixes():
                prev = tree
            tree = tree.children[words[i+1].replace(":","").replace(",","").replace("/","").replace("-","")]
        return tree.fullname, last_count

    def search_destroy(self, lst,threshold):
        franchises = {}
        for i in lst:
            try:
                to_remove = list(self.search(i))
                for title in to_remove[1]:
                    lst.remove(title)
                if len(to_remove[1]) > threshold:
                    last_words = []
                    for game in to_remove[1]:
                        last_word = game.split()[len(to_remove[0].split()) - 1]
                        last_words.append(last_word)
                    to_remove[0] = " ".join(to_remove[0].split()[0:len(to_remove[0].split()) - 1]) + " "+ Counter(last_words).most_common(1)[0][0]
                    franchises[to_remove[0]] = to_remove[1]
            except ValueError as e:
                # print(f"{e}: {title})")
                pass

        return franchises

    def all_titles(self, lst=None):
        if lst is None:
            lst = []
        for child in self.children.values():
            child.all_titles(lst)
        lst += self.titles
        return lst

