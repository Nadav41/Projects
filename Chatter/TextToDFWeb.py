import pandas as pd
import re
from Exceptions import DateError
from datetime import datetime, timedelta
import os
import zipfile
from collections import Counter

def get_participants(df):
    name_set = set()
    if df.empty:
        return ''
    for name in df['Author']:
        name_set.add(name)
    return ', '.join(list(name_set))

def split_whatsapp_chat(chat_text):
    chat_text = chat_text.replace("\u200E", "").replace("\u200F", "").replace('\n','.').replace('‬','').replace('\r','.')

    # Regular expression to detect message start: [DD/MM/YYYY, HH:MM:SS]
    pattern = r'\[\d{2}/\d{2}/\d{4}, \d{1,}:\d{1,}:\d{1,}\]'
    # Split only at points where a new message starts
    messages = re.split(f'(?={pattern})', chat_text)
    if len(messages) == 1:
        pattern = r'\[\d{2}.\d{2}.\d{4}, \d{1,}:\d{1,}:\d{1,}\]'
        messages = re.split(f'(?={pattern})', chat_text)
    return [msg.strip() for msg in messages if msg.strip()]

class TextDF:
    def __init__(self, enc=False, ready_str = None):
        self.__enc= enc
        self.extracted_folder = "extracted_files"
        self.__txt = ready_str.replace('\n','.').replace('\r','')
        data = {'Author': [] ,'Txt' :[],'Day' : [], 'Month' : [], 'Year' : [], 'Hour' : [], 'Minutes' : []}
        self.df = pd.DataFrame(data)
        self.__names = {}
        self.group_name = None #will change in make_text if chat has been since creation
        self.make_text(ready_str, enc)

        group_name = self.pop_group_name()
        if self.group_name is not None:
            group_name = self.group_name
        if len(self.__names) != 2:
            self.df = self.df[self.df['Author'] != group_name]
            self.__names.pop(group_name,None)
            print(self.__names.keys())
        if self.group_name is None:
            self.group_name = group_name
        print(self.group_name)

        # if enc:
        #     self.enc_Txt()

    def find_common_words(self):
        df = self.df.copy()
        df_grouped = df.groupby('Author', as_index = False).agg({'Txt': ' '.join})
        if len(self.__names) != 2:
            df_grouped = df_grouped[df_grouped['Author'] != self.group_name]
        df_grouped['Txt'] = df_grouped['Txt'].apply(lambda x: x.split())
        res_lst = []
        res_dict = {}
        for index, row in df_grouped.iterrows():
            aut = row['Author']
            res = find_top_5(row['Txt'])
            res_lst.append(f'{aut}: {res}')
            res_dict[row['Author']] = find_top_5(row['Txt'])
        return res_dict.items()

    def specific_author(self, name):
        df = self.df.copy()
        df = df[df['Author'] == name]
        # df['Author'] = df['Author'].apply(lambda x: 'MSG:')
        return df

    # def extract_zip(self,zip_path):
    #     """Extracts the ZIP file and returns the extracted file path(s)."""
    #     if not zipfile.is_zipfile(zip_path):
    #         raise ValueError("Provided file is not a valid ZIP file.")
    #
    #     # Create a folder to store extracted files
    #     os.makedirs(self.extracted_folder, exist_ok=True)
    #
    #     with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    #         zip_ref.extractall(self.extracted_folder)
    #
    #     # Get the extracted file paths
    #     extracted_files = [os.path.join(self.extracted_folder, f) for f in os.listdir(self.extracted_folder)]
    #     return extracted_files

    def get_names(self):
        return tuple(self.__names.keys())

    def max_time_window(self):
        df_copy = self.df.copy()
        df_copy['Time Window'] = (df_copy['Datetime'].dt.hour // 2) * 2
        df_copy['Time Window'] = df_copy['Time Window'].apply(lambda x: f"{x:02d}:00")
        # Count messages per time window and author
        time_activity = df_copy.groupby(['Author', 'Time Window']).size().reset_index(name='Message Count')

        most_active_idx = time_activity.groupby('Author')['Message Count'].idxmax().dropna()

        if most_active_idx.empty:
            return ()  # Return empty tuple if no valid data

        most_active = time_activity.loc[most_active_idx]
        if len(self.__names) != 2:
            most_active = most_active[most_active['Author'] != self.group_name]
        # Format the time window to include the end time of the 2-hour period
        most_active['Time Window'] = most_active['Time Window'].apply(
            lambda x: f"{x} - {int(x[:2]) + 2:02d}:00"
        )
        active_tups = [
            (row['Author'], row['Time Window'], f"{row['Message Count']} total messages")
            for _, row in most_active.iterrows()
        ]

        return tuple(active_tups)

    def pop_group_name(self):
        # Precompute regex pattern for names
        names_pattern = '|'.join(map(re.escape, self.__names))

        # Compute mask in a single operation
        mask = ~(self.df['Txt'].str.contains('changed the group description', na=False) & ~(
            (self.df['Txt'].str.contains('updated', na=False)| self.df['Txt'].str.contains('removed', na=False)) &
                self.df['Txt'].str.contains(names_pattern, na=False)) & (self.df['Txt'].str.contains('צורפת על ידי', na=False) & ~(
            (self.df['Txt'].str.contains('updated', na=False)| self.df['Txt'].str.contains('removed', na=False)) &
                self.df['Txt'].str.contains(names_pattern, na=False))))

        # Extract removed authors before filtering
        removed_authors = [i for i in self.df.loc[~mask, 'Author'].unique().tolist() if self.df.loc[mask][self.df['Author']==i].empty]

        # Efficiently filter DataFrame
        self.df = self.df.loc[mask].reset_index(drop=True)  # Drop unneeded index references
        if removed_authors != []:
            return removed_authors[0]  # Return removed authors
        return ''

    def open_txt(self,path):
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()  # Reads the entire file content
            return content  # Prints the content of the file

    # def prepare_text(self,path):
    #     return self.open_txt(path).replace('\n','')

    # def reg_time(self):
    #     reg_list = re.findall(r'\[\d{2}/\d{2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\]', self.__txt)
    #     return reg_list

    # def reg_txt(self):
    #     reg_list = re.findall(r'\[\d{2}/\d{2}/\d{4},\s\d{2}:\d{2}:\d{2}\]', self.__txt)
    #     return reg_list

    def make_text(self,ready_str,flag = False):
        for i in split_whatsapp_chat(ready_str):
            time = i[:22]
            time = self.split_time(time)
            i = i[22:]
            # print(i)
            start = i.index(':')
            message = i[start + 2:]
            author = i[:start]
            if 'Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to the' in message or "ההודעות והשיחות מוצפנות מקצה לקצה. לאף אחד מחוץ לצ'אט הזה" in message:
                self.group_name = ' '.join(re.findall(r'(\S+)', author))
                continue
            self.df.loc[len(self.df)] = self.enc(author, message, flag) + time
        self.df[["Year", "Month", "Day", "Hour", "Minutes"]] = self.df[["Year", "Month", "Day", "Hour", "Minutes"]].astype(int)
        # Convert dataframe timestamps to datetime objects
        self.df["Datetime"] = self.df.apply(lambda row: datetime(row["Year"], row["Month"], row["Day"], row["Hour"], row["Minutes"]), axis=1)


    def enc(self, author, message, flag):
        self.__coded_names = [
        "Alex", "Sam", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Quinn", "Jamie", "Avery",
        "Sky", "River", "Phoenix", "Sage", "Dakota", "Rowan", "Finley", "Blair", "Emery", "Aspen",
        "Cameron", "Drew", "Logan", "Charlie", "Elliot", "Parker", "Reese", "Micah", "Noel", "Hayden",
        "Dakota", "Shawn", "Jesse", "Frankie", "Max", "Adrian", "Corey", "Devon", "Lane", "Blake",
        "Ari", "Dallas", "Skyler", "Marley", "Kai", "Toby", "Ellis", "Peyton", "Remy", "Oakley",
        "Emerson", "Kendall", "Harley", "Sterling", "Sasha", "Jordan", "Dylan", "Case", "Hollis", "Blaine",
        "Shiloh", "Rory", "Kieran", "Payton", "Robin", "Jules", "Tristan", "August", "Ellery", "Arden",
        "Justice", "Rowe", "Winter", "Cam", "Haven", "Linden", "Ocean", "Sutton", "Ever", "Brighton",
        "Harlow", "Onyx", "Vale", "Salem", "Denim", "Indigo", "Lake", "Paris", "Ridley", "Storm",
        "West", "Lior", "Echo", "Sparrow", "Cypress", "Horizon", "Zephyr", "Zen", "Nova", "Briar"]
        author = (' '.join(re.findall(r'(\S+)', author)))
        self.__names[author] = ''
        if flag:
            if author not in self.__names:
                self.__names[author] = self.__coded_names[len(self.__names)]
            return [self.__names[author], message]
        return [author, message]


    def split_time(self,date):
        return [int(block) for block in re.findall(r'(\d{1,4})',date)][:-1]

    def count_by_week(self):
        df = self.df.copy()

        df["Week_Period"] = df["Datetime"].dt.to_period("W-SAT")

        weekly_counts = df.groupby("Week_Period").agg(
            Message_Count=("Datetime", "count")
        ).reset_index()

        weekly_counts["Week_Start"] = weekly_counts["Week_Period"].apply(lambda x: x.start_time)
        weekly_counts["Week_End"] = weekly_counts["Week_Period"].apply(lambda x: x.end_time)

        # Get today's date as a Timestamp
        today = pd.Timestamp.today()
        # Convert today's date to the weekly period (with weeks ending on Saturday)
        current_week_period = today.to_period("W-SAT")

        # Find data for the current week
        current_week_data = weekly_counts[weekly_counts["Week_Period"] == current_week_period]
        if not current_week_data.empty:
            current_week_count = current_week_data["Message_Count"].iloc[0]
        else:
            current_week_count = 0

        # Print current week info using the period's start and end dates
        res_str = ''
        res_str +=f"This week ({current_week_period.start_time.strftime('%d/%m/%Y')} - {current_week_period.end_time.strftime('%d/%m/%Y')}):<br>{current_week_count} messages\n"

        # Sort the weeks by message count in descending order and take the top 5 weeks
        top_weeks = weekly_counts.sort_values(by="Message_Count", ascending=False).head(5).reset_index(drop=True)

        res_str += "Top 5 weeks:\n"
        for idx, row in top_weeks.iterrows():
            start_str = row["Week_Start"].strftime("%d/%m/%Y")
            end_str = row["Week_End"].strftime("%d/%m/%Y")
            res_str += f"{idx + 1}: {start_str} - {end_str}: {row['Message_Count']} messages\n"

        return res_str

    def enc_Txt(self):
        self.df['Txt'] = self.df['Txt'].apply(lambda message: self.enc_message(message))

    def start_from(self, start_date):
        df = self.df.copy()  # Prevent modifying the original DataFrame
        hour, minutes, day, month, year = start_date
        start_time = datetime(year, month, day, hour, minutes)

        # Filter the DataFrame to include only messages after the given time
        df = df[df["Datetime"] >= start_time]
        # If no messages remain, raise an error
        if df.empty:
            raise DateError((hour, minutes), (day, month, year))

        return df  # Return the filtered DataFrame

    def end_at(self,end_date, df):
        hour, minutes, day, month, year = end_date
        end_time = datetime(year, month, day, hour, minutes)


        df = df[df["Datetime"] <= end_time]
        # If no messages remain, raise an error
        if df.empty:
            raise DateError((hour, minutes), (day, month, year))
        return df

    def dec_message(self,msg):
        if self.__enc:
            for key, item in self.__names.items():
                msg = msg.replace(item, key)
            dot_count = 0
            i = 0
            new = ''
            while i < len(msg) - 1:
                new += msg[i]
                if msg[i] == '.':
                    if dot_count % 2 == 0:
                        new += '\n'
                        i+=1
                    dot_count += 1
                i += 1
            return new
        return msg


    def enc_message(self, msg):
        for author in self.__names:
            f_name = author.split(' ')[0]
            for word in msg.split(' '):
                if 0 <= len(word) - len(f_name) <= 2:
                    if word.startswith(f_name):
                        msg = msg.replace(word, self.__names[author] + word[len(f_name):])
                    elif word.endswith(f_name):
                        msg = msg.replace(word, self.__names[author] + word[:len(word) - len(f_name)])

        return msg

    def df_to_text(self, df = None):
        if df is not None and not df.empty:
            str = ''
            for index, row in df.iterrows():
                new = f" {row['Author']}: {row['Txt']}"
                if len(str) + len(new) > 4500:
                    break
                str += new
            return str
        return "".join(self.df.apply(lambda row: f"{row['Author']}: {row['Txt']}", axis=1))

    def count_per_author(self):
        df = self.df.copy()
        counts = df['Author'].value_counts().to_dict()
        if len(self.__names) != 2:
            df = df[df['Author'] != self.group_name]
        sum_counts = sum(counts.values())
        return sum_counts, counts

def find_top_5(words_list):
    words_list = [x for x in words_list if len(x) > 3 and x.count(x[0]) < len(x) - 2 and x not in ('omitted..','image','You received a view once photo. For added privacy, you can', 'audio','was','added','message', 'edited>', 'sticker', 'your','<This','votes).OPTION','received', 'pages document','<This>','view', '<This>', 'once', 'For added privacy, you can','only open it on your phone.', 'privacy,', 'only', 'open', 'phone.','photo.', 'omitted.. ')]
    res_lst = tuple(Counter(words_list).most_common(10))
    return res_lst
