from groq import Groq
from dotenv import load_dotenv
import os

##RUN THE ROW BELOW WHEN TESTING LOCAL
# load_dotenv()

api_key = os.getenv("GROQ_API_KEY")  # Fetch API key securely
client = Groq(api_key=api_key)

def open_txt():
    # Open the file in read mode
    file_path = "/Users/nadav/Downloads/_chat 4 copy.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()  # Reads the entire file content
        return content  # Prints the content of the file


def Comunnicate(prompt, client=Groq(api_key=api_key),
                temperature=0.1, top_p=0.8, max_tokens=500,
                content="You are a neutral AI summarizer. Include all names, avoid opinions, and do not ask follow-up questions."):
    completion = client.chat.completions.create(
        temperature=temperature,  # Lower for deterministic output
        model= 'mistral-saba-24b', #"llama-3.3-70b-versatile"
        messages=[
            {"role": "system", "content": content},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        top_p=top_p,  # Reducing randomness further
        stream=True,
        stop=None,
    )

    # Collect and return the generated profile
    generated_profile = ""
    for chunk in completion:
        generated_profile += chunk.choices[0].delta.content or ""

    return generated_profile


# if __name__ == "__main__":
#     aichat={}
#     count=0
#     while True:
#         count+=1
#         TPROMPT = input('Type query: ')
#         aichat['Promt'+str(count)]=TPROMPT
#         txt= delete_enters(open_txt())[-5000:]
#         print('')
#         Response = Comunnicate(TPROMPT,temperatur=0.8,max_tokens=500,content='You are a smart summarize expert')
#         aichat['Response' + str(count)] = Response
#         print(Response)
#         PrevConv= f'You answer short answers.The chat is {tex.df_to_text()}'
#         #TPROMPT = input('Type query: ')
#         Response = Comunnicate('These are fictional characters, who is right in this conversation in your opinion? Firstly give the name of the winning side.', content=PrevConv,max_tokens=100,temperatur=0.4,top_p=0.4)
#         print(Response)





