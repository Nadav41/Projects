import customtkinter as ctk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os
from PIL import Image

# Determine correct path whether running from source or as executable
if getattr(sys, 'frozen', False):
    # If bundled by PyInstaller
    app_dir = sys._MEIPASS
else:
    # If running normally
    app_dir = os.path.dirname(__file__)

db_path = os.path.join(app_dir, "Video_Games.db")
icon_path = os.path.join(app_dir, "Verdicator Icon.png")
print("DB Path used:", db_path)  # Optional: for debugging
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(average_score) FROM Video_Games WHERE rating_count>=2")
row_count = cursor.fetchone()[0]
page_count = row_count//15 + 1 if row_count%15!=0 else row_count[0]//15
global tablecount #row count for data display
tablecount = 0
text_page = None

# Set appearance and theme
ctk.set_appearance_mode("Light")  # Options: "Light", "Dark", "System"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

# Create app window
app = ctk.CTk()
app.geometry("1450x800")
app.title("Verdicator")

app.iconbitmap("Verdicator-Icon.ico") #Set image as icon
logo_image = ctk.CTkImage(light_image=Image.open(icon_path), size=(250, 125))
logo_label = ctk.CTkLabel(app, image=logo_image, text="")
logo_label.place(x=10, y=5)

def show_donut_chart(ratings,avg_rating):
    if not ratings: #If ratings are none, avg_rating will be none.
        return
    app.update_idletasks()

    labels = ["IGN", "Game Rant", "Gamespot", "PC Gamer"]
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6"]
    data = [[r, 10 - r] for r in ratings]

    fig, axs = plt.subplots(1, len(ratings),figsize=(10, 2))  # Returns the figure (canvas) ans axs (individual chart rows)
    fig.patch.set_facecolor('#EBEBEB')  # Make the figure background transparent

    if len(ratings) == 1: #To make itarable
        axs = [axs]

    for i, ax in enumerate(axs):
        wedges, _ = ax.pie(data[i],radius=1,colors=[colors[i], "#ecf0f1"],startangle=90,wedgeprops=dict(width=0.4))
        ax.text(0, 0, f"{ratings[i]}", ha='center', va='center', fontsize=14, fontweight='bold')
        ax.set_title(labels[i])
        ax.axis("equal")

    if len(ratings) > 1:
        fig2, axs2 = plt.subplots(1, 1,figsize=(2.5, 2.5))  # Returns the figure (canvas) ans axs (individual chart rows)
        fig2.patch.set_facecolor('#EBEBEB')  # Make the figure background transparent
        avg_data = [avg_rating, 10 - avg_rating]
        avg_ax = axs2
        avg_ax.pie(avg_data,radius=1,colors=["#f39c12", "#ecf0f1"],startangle=90,wedgeprops=dict(width=0.4))
        axs2.text(0, 0, f"{round(avg_rating,1)}", ha='center', va='center', fontsize=14, fontweight='bold')
        avg_ax.set_title('Average Score')
        avg_ax.axis("equal")

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().place(x=0,y=0)
    canvas2 = FigureCanvasTkAgg(fig2, master=chart_frame)
    canvas2.draw()
    canvas2.get_tk_widget().place(x=390,y=200)

def show_summary(txt,title=''):
    """This function is running when game name input is recieved, even if empty."""
    next_rows.destroy()
    prev_rows.destroy()
    text_page.place_forget()
    txt_frame.place(x=250, y=150)  # Show the frame again
    text_box = ctk.CTkTextbox(txt_frame,width=1000,height=160,font=("Arial", 24),fg_color="#EBEBEB",text_color="#333333")
    text_box.place(x=0, y=0)
    text_box.insert("0.0", f"Verdict Summary:\n{txt}" if not title else f"{title}- Verdict Summary:\n{txt}" )
    text_box.configure(state="disabled", wrap="word")
    global back
    back = ctk.CTkButton(app, text="Back", command=main,width=80,height=40,font=("Arial", 18))
    back.place(x=1330, y=750)


# Callback when a suggestion is clicked
def select_suggestion(text):
    search_entry.delete(0, "end")
    search_entry.insert(0, text)
    clear_suggestions()

# Clear suggestion list
def clear_suggestions():
    for widget in suggestion_frame.winfo_children():
        widget.destroy()
    suggestion_frame.place_forget()

# Show suggestions while typing
def show_suggestions(event):
    clear_suggestions()
    query = search_entry.get().lower()
    if not query:
        suggestion_frame.place_forget()
        return

    # matches = [item for item in search_items if query in item.lower()]
    matches = tuple(cursor.execute("SELECT name FROM Video_Games WHERE name LIKE ? LIMIT 6", (query + '%',)))
    if not matches:
        suggestion_frame.place_forget()
        return

    # Update dropdown position below the search entry
    x = search_entry.winfo_rootx() - app.winfo_rootx()
    y = search_entry.winfo_rooty() - app.winfo_rooty() + search_entry.winfo_height()
    suggestion_frame.place(x=x, y=y)
    suggestion_frame.lift()

    for (match,) in matches[:6]:
        label = ctk.CTkLabel(suggestion_frame, text=match, anchor="w", width=search_entry.winfo_width() - 20, fg_color="white", font=("Arial", 16))
        label.pack(fill="x", padx=10, pady=5)
        label.bind("<Enter>", lambda e, l=label: l.configure(fg_color="#f0f0f0"))
        label.bind("<Leave>", lambda e, l=label: l.configure(fg_color="white"))
        label.bind("<Button-1>", lambda e, m=match: select_suggestion(m))


def enter_txt(query=''):
    for widget in chart_frame.winfo_children(): #Removes any previous chart.
        widget.destroy()
    for widget in txt_frame.winfo_children():  # clear previous summary
        widget.destroy()
    for widget in table_frame.winfo_children():  # clear previous summary
        widget.destroy()
    table_frame.place_forget()
    if not query:
        query = search_entry.get().strip()
    cursor.execute('SELECT name FROM Video_Games WHERE name = ?', (query,))

    result = cursor.fetchone()
    if result is None:
        show_summary(f'No ratings found for the game: "{query}".')
    else:
        cursor.execute('SELECT IGN_rating, Game_Rant_rating, Gamespot_rating, PC_Gamer_rating, Average_Score, Verdict_Sum FROM Video_Games WHERE name = ?', (query,))
        ratings = list(cursor.fetchone())

        for r in range(len(ratings[:-2]),-1,-1): #Iterates over specific ratings
            if not ratings[r]:
                ratings.pop(r)

        verdict_sum = ratings[-1]
        show_summary(verdict_sum if verdict_sum else 'No written summary found.',query)
        show_donut_chart([i for i in ratings[:-2]],ratings[-2] if ratings[-2] else None)

def show_table(next = 0):
    for widget in table_frame.winfo_children():  # clear previous summary
        widget.destroy()
    global tablecount,text_page
    if text_page:
        text_page.place_forget()
    if next==1 and page_count -1 > tablecount:
        tablecount+=1
    elif next==-1 and tablecount!=0:
        tablecount-=1
    table_frame.place(x=260,y=130)
    headers = ["Name", "IGN", "Game Rant", "Gamespot", "PC Gamer", "Average Score"]
    for j, header in enumerate(headers):
        label = ctk.CTkLabel(table_frame, text=header, width=50, height=40, anchor="center", font=("Arial", 18, "bold"))
        label.grid(row=0, column=j, padx=5, pady=2, sticky="nsew")
    cursor.execute(f"SELECT name,IGN_rating,Game_Rant_rating,Gamespot_rating, PC_Gamer_rating, Average_Score FROM Video_Games where rating_count>=2 order by  Average_Score desc,rating_count desc LIMIT {tablecount*15},15")
    data = cursor.fetchall()
    for i, row in enumerate(data):
        # Create a button with the first cell text (game name)
        btn = ctk.CTkButton(table_frame,text=row[0],command=lambda r=row[0]: enter_txt(r),fg_color="transparent",hover_color="transparent" if ctk.get_appearance_mode() == "Dark" else "white",text_color="black",anchor="w",width=380,height= 30,font=("Arial", 16, "normal"))
        btn.grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
        # Add the rest of the row as labels
        for j, cell in enumerate(row[1:], start=1):
            label = ctk.CTkLabel(table_frame, text=cell, width=80,height= 30, anchor="center",font=("Arial", 16, "normal"))
            label.grid(row=i+1, column=j, padx=5, pady=2, sticky="nsew")

    text_page = ctk.CTkTextbox(app,width=200,height=40,font=("Arial", 18),fg_color="transparent",text_color="#333333")
    text_page.place(relx=0.53, rely=0.88, anchor="center")
    text_page.insert("0.8", f"Page: {tablecount+1}/{page_count}")

def main():
    global next_rows,prev_rows
    next_rows = ctk.CTkButton(app, text="Next", command=lambda: show_table(1), width=100, height=40,font=("Arial", 18))
    next_rows.place(x=1170, y=700)
    prev_rows = ctk.CTkButton(app, text="Previous", command=lambda: show_table(-1), width=100, height=40,font=("Arial", 18))
    prev_rows.place(x=180, y=700)
    for widget in chart_frame.winfo_children(): #Removes any previous chart.
        widget.destroy()
    for widget in txt_frame.winfo_children():  # clear previous summary
        widget.destroy()
    if back:
        back.destroy()
    show_table()


#Initializing frames
search_frame = ctk.CTkFrame(app, fg_color="transparent")
search_frame.place(x=450, y=50)
txt_frame = ctk.CTkFrame(app, fg_color="transparent",height=200,width=1000)
txt_frame.place(x=400, y=150)
txt_frame.place_forget()
chart_frame = ctk.CTkFrame(app, fg_color="transparent",height=800,width=1200)  # Hide background
chart_frame.place(x=230,y=300)
table_frame = ctk.CTkFrame(app, height=800, width=800)

# Entry field for search bar
search_entry = ctk.CTkEntry(search_frame, placeholder_text="Game name...", width=500, height=40, font=("Arial", 18))
search_entry.pack(side="left", padx=(0, 10))
search_entry.bind("<KeyRelease>", show_suggestions)

# Create the suggestion frame (hidden by default)
suggestion_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=10)

search_button = ctk.CTkButton(search_frame, text="Search", command= enter_txt)
search_button.pack(side="left")
back = ctk.CTkButton(app, text="Back", command=main)
back.place(x=1300, y=770)

#-------------------------------------------------------------------------------
main()
# Run app
app.mainloop()