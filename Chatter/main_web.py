from TextToDFWeb import TextDF, get_participants
from datetime import datetime
from Exceptions import DateError
from API import Comunnicate
import re

def extract_reduced_conversation(text): #Taken form ChatGPT, takes 3 sentences out of 9
    # Split text into sentences using ":" as the primary separator
    sentences = re.split(r'(?<=[:])\s*', text)  # Keeps ":" at the end of each sentence

    # Process in chunks of 9, selecting 3 strategically
    reduced_sentences = []
    for i in range(0, len(sentences), 9):  # Process in blocks of 9
        chunk = sentences[i:i + 9]  # Get 9 sentences (or fewer at the end)

        if len(chunk) >= 3:
            # Pick sentences: first, middle, and last (adjust if fewer than 9)
            reduced_sentences.append(chunk[0])  # First sentence
            reduced_sentences.append(chunk[len(chunk) // 2])  # Middle sentence
            reduced_sentences.append(chunk[-1])  # Last sentence
        else:
            # If less than 3 remaining, just add all
            reduced_sentences.extend(chunk)

    # Join the reduced sentences back
    reduced_text = " ".join(reduced_sentences)
    return reduced_text
now = datetime.now()
print(now)


class interface:
    def __init__(self,ready_str,enc = False):
        self.df = TextDF(ready_str = ready_str, enc = enc)
        self.__is_enc = enc

    def sum_chat(self, lang, start_time, end_time):
        chat = self.get_df(start_time,end_time)
        if chat is not None:
            txt = chat[1]
            if lang == '1':
                print('\nAI response:\n')
                answer = self.df.dec_message(Comunnicate(
                    prompt=f"Summarize the following chat factually in **no more than 2 sentences**. Do not ask questions. Be concise. Do not add opinions, explanations, or unnecessary details. Chat: {txt}",
                    temperature=0.4, max_tokens=200, content='You are a smart summarize expert'))
            else:
                print('\nAI response:\n')
                answer = self.df.dec_message(Comunnicate(
                    prompt = f"השב בעברית בלבד. השב רק בשני משפטים. אל תוסיף הסברים או דעות. הזכר את כל שמות המשתתפים. שיחה: {chat[1]}",
                    temperature=0.4, max_tokens=200, content='You are a smart summarize expert'))
            print(get_participants(chat[0]))
            print('chat:' + txt)
            print(answer)

            return 'Participants: '+get_participants(chat[0]) + '<br><br>' + answer.replace('.', '.<br>')
        return ''

    def arg_chat(self, lang, start_time,end_time):
        chat = self.get_df(start_time,end_time)[1]
        if lang == '1':
            print('\nAI response:\n')
            answer = self.df.dec_message(Comunnicate(
                prompt=f"Analyze the following conversation factually and determine who is correct based on the statements given. Provide only the name of the correct person and a two-sentences short explanation. Do not add opinions. Chat: {chat}",
                temperature=0.3, max_tokens=200, content='You are a smart summarize expert')) + '.'
        else:
            print('\nAI response:\n')
            answer = self.df.dec_message(Comunnicate(
                prompt=f"תנתח את השיחה הבאה באופן עובדתי ותקבע מי צודק בהתבסס על הטענות שנאמרו. ציין רק את שם האדם הצודק ותן הסבר במשפט אחד בלבד. אל תוסיף דעות. שיחה: {chat}",
                temperature=0.4, max_tokens=200, content='You are a smart summarize expert')) + '.'
        return answer

    def get_df(self,start_time ,end_time):
        try:
            chatdf = self.df.start_from(start_time)
            if end_time is not None:
                chatdf = self.df.end_at(end_time, chatdf)
            return chatdf, self.df.df_to_text(chatdf).replace('\r','').encode("utf-8").decode("utf-8")  # Normalize encoding
        except DateError as e:
            return None
    def sum_author(self, name):
        df = self.df.specific_author(name)
        chat = self.df.df_to_text(df).replace('\r','')
        chat = extract_reduced_conversation(chat)
        answer1 = self.df.dec_message(Comunnicate(
            prompt=f"**Begginer English level** Analyze the personality and communication style of the author based on the messages provided. Describe their vibe **in one sentence**, making it unique to their tone, word choice, and message patterns. Avoid generic statements. Messages: {chat}",
            temperature=0.4, max_tokens=100,
            content="You specialize in analyzing personalities and providing precise, distinct, and insightful summaries. giving simple understandable words"))
        answer2 = self.df.dec_message(Comunnicate(
            prompt=f"**Easy English** Summarize the general tone and subjects of the chats sent. **two sentences**. Messages: {chat}",
            temperature=0.5, max_tokens=100,
            content="You specialize in analyzing chats and providing precise, distinct, and insightful summaries. giving simple understandable words"))
        return answer1,answer2

    def is_funny(self, name):
        df = self.df.specific_author(name)
        chat = self.df.df_to_text(df).replace('\r', '')
        chat = extract_reduced_conversation(chat)
        print(len(chat))

        answer = self.df.dec_message(Comunnicate(
            prompt=f"**Fair and Constructive Humor Check** Analyze the chat messages from this author and determine if they are funny. Since there are no messages from others, judge their humor based only on their writing style. Respond in **one sentence only**. If their messages contain humor, sarcasm, or jokes, say 'Yes' and include their funniest message as an example. If they try to be funny but don’t quite succeed, say 'Not really' and include an example of a message where they attempted humor but it wasn’t very strong. If there is no humor at all, say 'No' and provide a neutral and constructive statement about their writing style, avoiding harshness. Messages: {chat}",
            temperature=0.7, max_tokens=75,
            content="Give a fair and constructive assessment of the author's humor. Always provide an example from their messages. Avoid being overly harsh—if they try, acknowledge it politely. Respond in one sentence only."
        ))
        return answer
