import pandas as pd
import sqlite3
from collections import Counter

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.titles = []
        self.children = {}
        self.depth = 0 #Initial height
        self.fullname = ""

    def add_child(self, new):
        words = new.split()
        if len(words) == self.depth or (self.depth + 1 == len(words) and words[self.depth].isnumeric()):
            self.titles.append(new)
            return
        word = new.split()[self.depth].replace(":","").replace(",","").replace("/","").replace("-","")
        if word not in self.children:
            new_tree = TreeNode(word)
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

    def search_destroy(self, lst):
        franchises = {}
        for i in lst:
            try:
                to_remove = list(self.search(i))
                for title in to_remove[1]:
                    lst.remove(title)
                if len(to_remove[1]) > 30:
                    last_words = []
                    for game in to_remove[1]:
                        last_word = game.split()[len(to_remove[0].split()) - 1]
                        last_words.append(last_word)
                    to_remove[0] = " ".join(to_remove[0].split()[0:len(to_remove[0].split()) - 1]) + " "+ Counter(last_words).most_common(1)[0][0]
                    franchises[to_remove[0]] = to_remove[1]
            except ValueError as e:
                print(f"{e}: {title})")

        return franchises

    def all_titles(self, lst=None):
        if lst is None:
            lst = []
        for child in self.children.values():
            child.all_titles(lst)
        lst += self.titles
        return lst


conn = sqlite3.connect('Video_Games.db')
df = pd.read_sql("SELECT * FROM Video_Games", conn)
words = {}

for title in df["name"]:
    for word in title.split():
        words[word] = words.get(word,0) + 1

# wordict = {}
titles = list(df["name"])
titles2 = ["Call of Duty","Call: of Duty 2", "Call of- Duty king", "Call of Juarez"]
tree = TreeNode("*")
for title in titles2:
    tree.add_child(title)
# print(tree.all_titles())

# tree2 = tree.search("Call: of Duty 2")
# print(tree2)


tree = TreeNode("*")
for title in titles:
    tree.add_child(title)
print(tree.search("Final Fantasy Fables: Chocobo's Dungeon")[0])  # Final Fantasy
print(tree.search("Call of Duty: Black Ops 3")[0])                # Call of Duty
print(tree.search("Assassin's Creed Revelations")[0])             # Assassin's Creed
print(tree.search("LEGO Star Wars II: The Original Trilogy")[0])  # LEGO Star Wars
print(tree.search("The Sims: Bustin' Out")[0])                    # The Sims
# print(tree.search("Call of Duty Modern Warfare"))  # → should return all Call of Duty titles
# print(tree.search("Grand Theft Auto V"))           # → GTA titles
# print(tree.search("Assassin's Creed"))
f = tree.search_destroy(titles)
print(f)




# toremove = []
# i=0
# while True:
#     for title in titles:
#         if len(" ".join(title)) > i:
#             title = title.split()
#             sub_name = " ".join(title[:i + 1])
#             if sub_name == "Call":
#                 pass
#             wordict[sub_name] = wordict.get(sub_name, (i, []))
#             wordict[sub_name][1].append(" ".join(title))
#     for j in range(len(titles)):
#         sub_name = " ".join(titles[j].split()[:i+1])
#         if sub_name in wordict and len(wordict[sub_name][1]) == 1: #Removes the
#             toremove.append(j)
#             wordict.pop(sub_name)
#     for k in range(len(toremove),-1,-1):
#         titles.pop(k)
#     toremove = []
#     i+= 1
#     if i == len(df["name"]) or titles == []:
#         break
# print(wordict)



# for title in df["name"]:
#     insert(trie,title.split())
# print_trie(trie)

# for title in df["name"]:
#     for word in title.split():
#         words[word] = words.get(word,0) + 1
# # print(words)
# words2 = {}
# for word, count in words.items():
#     if count > 10:
#         words2[word] = words[word]
#
# print(list(words2.items()))
# print(sorted(list(words2.items()),key= lambda x: x[1],reverse=True))
# df.to_csv("Video Games CSV.csv", index = False)