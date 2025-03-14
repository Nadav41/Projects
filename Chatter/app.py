from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from main_web import interface
from dateutil import parser
import datetime
import os
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for sessions

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global dictionary to hold per-user data (keyed by user_id)
user_data = {}


def get_user_id():
    """
    Retrieve a unique user_id from the session. If none exists, create one.
    """
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    return session["user_id"]

def detect_language(text):
    hebrew_count = sum(1 for c in text if "\u0590" <= c <= "\u05FF")  # אותיות עבריות
    english_count = sum(1 for c in text if "A" <= c <= "Z" or "a" <= c <= "z")  # אותיות באנגלית

    return "rtl" if hebrew_count > english_count else "ltr"



@app.route("/", methods=["GET"])
def home():
    # דף הבית: מציג את הקובץ "zip extract.html" עם אפשרות העלאת קובץ ZIP.
    return render_template("zip extract.html")


@app.route("/process_text", methods=["POST"])
def process_text():
    """
    ראוט שמקבל את המחרוזת שהופקה מהקובץ (באמצעות JSZip בצד הלקוח)
    ויוצר ממנה את text_processor עבור המשתמש.
    """
    user_id = get_user_id()
    data = request.json
    extracted_text = data.get("text", "")
    if not extracted_text:
        return jsonify({"error": "No text received"}), 400

    # ייצור מעבד הטקסט בעזרת הפונקציה interface, שמקבלת את המחרוזת
    user_data[user_id] = {
        "text_processor": interface(ready_str=extracted_text),
        "sum_res": None,
        "arg_res": None,
        "start_date": None,
        "end_date": None
    }

    return jsonify({"message": "Processor created", "text": extracted_text})

@app.route("/manual")
def manual():
    return render_template("Manual.html")

@app.route('/menu')
def menu():
    user_id = get_user_id()
    # Reset previous results and date selections for a fresh start.
    if user_id in user_data:
        user_data[user_id]["sum_res"] = None
        user_data[user_id]["arg_res"] = None
        user_data[user_id]["start_date"] = None
        user_data[user_id]["end_date"] = None
        user_data[user_id]["chosen_name"] = None
    title = user_data[user_id]['text_processor'].df.group_name
    if title == '':
        name_list = user_data[user_id]['text_processor'].df.get_names()
        if len(name_list) == 2:
            title = f'{name_list[0]} | {name_list[1]}'
    return render_template('menu.html', title = title)



@app.route('/sum_eng')
def sum_eng():
    try:
        user_id = get_user_id()
        if user_id not in user_data or user_data[user_id].get("text_processor") is None:
            return render_template('error.html', message="No ZIP file was uploaded.")

        if user_data[user_id].get("start_date") is None or user_data[user_id].get("end_date") is None:
            return redirect(url_for('select_dates', next_action='sum_eng'))

        tp = user_data[user_id]["text_processor"]
        sum_res = tp.sum_chat(lang='1', start_time=user_data[user_id]["start_date"], end_time=user_data[user_id]["end_date"])
        user_data[user_id]["sum_res"] = sum_res
        if sum_res == '':
            return render_template('error.html', message="No messages in time range.")
        text_direction = detect_language(sum_res)
        date_tuple = (user_data[user_id]["start_date"],user_data[user_id]["end_date"])
        print(date_tuple)
        dates_str = f'{datetime.datetime(date_tuple[0][4], date_tuple[0][3], date_tuple[0][2], date_tuple[0][0], date_tuple[0][1]).strftime("%d/%m/%Y %H:%M")} - '
        if date_tuple[1] is None:
            dates_str += 'Today'
        else:
            dates_str += datetime.datetime(date_tuple[1][4], date_tuple[1][3], date_tuple[1][2], date_tuple[1][0], date_tuple[1][1]).strftime("%d/%m/%Y %H:%M")
        print(dates_str)
        return render_template('text_template.html', page_title='AI Summary of Chat', page_content=sum_res, direction=text_direction, dates = dates_str)
    except:
         return render_template('error.html', message="Out of free AI tokens.. Try later!")

@app.route('/arg_eng')
def arg_eng():
    try:
        user_id = get_user_id()
        if user_id not in user_data or user_data[user_id].get("text_processor") is None:
            return render_template('error.html', message="No ZIP file was uploaded.")

        if user_data[user_id].get("start_date") is None or user_data[user_id].get("end_date") is None:
            return redirect(url_for('select_dates', next_action='arg_eng'))

        tp = user_data[user_id]["text_processor"]
        arg_res = tp.arg_chat(lang='1', start_time=user_data[user_id]["start_date"], end_time=user_data[user_id]["end_date"])
        user_data[user_id]["arg_res"] = arg_res

        return render_template('text_template.html', page_title='Who is Right?', page_content=arg_res)
    except:
         return render_template('error.html', message="Out of free AI tokens.. Try later!")
@app.route("/week_count")
def week_count():
    user_id = get_user_id()
    if user_id not in user_data or user_data[user_id].get("text_processor") is None:
        return render_template('error.html', message="No ZIP file has been uploaded yet!")

    result = user_data[user_id]["text_processor"].df.count_by_week().split("\n")

    return render_template("message count.html", result=result)

@app.route("/name_count")
def name_count():
    user_id = get_user_id()
    if user_id not in user_data or user_data[user_id].get("text_processor") is None:
        return render_template('error.html', message="No ZIP file has been uploaded yet!")
    sum, count = user_data[user_id]["text_processor"].df.count_per_author()
    count = count.items()
    result = [f'There was total of: {sum} messages.']
    for name, count in count:
        result += [f'{name}:  {count} messages.']
    return render_template("name count.html", result=result)


@app.route("/author_sum")
def author_sum():
    try:
        user_id = get_user_id()

        # Ensure user data exists
        if user_id not in user_data or user_data[user_id].get("text_processor") is None:
            return render_template('error.html', message="No ZIP file has been uploaded yet!")

        # Get the selected name from the query params (from JavaScript)
        selected_option = request.args.get("choice")

        if selected_option:
            user_data[user_id]["chosen_name"] = selected_option  # ✅ Store the selected name

        # Ensure a name is selected
        if user_data[user_id].get("chosen_name") is None:
            return redirect(url_for('select_name', next_action='author_sum'))  # Ask user to select

        # Get the chosen name & analyze the data
        name = user_data[user_id]["chosen_name"]
        res_tup = user_data[user_id]["text_processor"].sum_author(name)  # ✅ Get results

        return render_template("author sum.html", result=res_tup, url = '/author_sum')  # ✅ Display results
    except:
         return render_template('error.html', message="Out of free AI tokens.. Try later!")
@app.route("/is_funny")
def is_funny():
    try:
        user_id = get_user_id()

        # Ensure user data exists
        if user_id not in user_data or user_data[user_id].get("text_processor") is None:
            return render_template('error.html', message="No ZIP file has been uploaded yet!")

        # Get the selected name from the query params (from JavaScript)
        selected_option = request.args.get("choice")

        if selected_option:
            user_data[user_id]["chosen_name"] = selected_option  # ✅ Store the selected name

        # Ensure a name is selected
        if user_data[user_id].get("chosen_name") is None:
            return redirect(url_for('select_name', next_action='is_funny'))  # Ask user to select

        # Get the chosen name & analyze the data
        name = user_data[user_id]["chosen_name"]
        res_tup = user_data[user_id]["text_processor"].is_funny(name)  # ✅ Get results

        return render_template("is funny.html", result=res_tup, name = name)  # ✅ Display results
    except:
         return render_template('error.html', message="Out of free AI tokens.. Try later!")
@app.route("/time_windows")
def time_windows():
    user_id = get_user_id()
    if user_id not in user_data or user_data[user_id].get("text_processor") is None:
        return render_template('error.html', message="No ZIP file has been uploaded yet!")
    res_tup = user_data[user_id]["text_processor"].df.max_time_window()
    return render_template("Time Window.html", result=res_tup)

@app.route("/word_count")
def word_count():
    user_id = get_user_id()
    if user_id not in user_data or user_data[user_id].get("text_processor") is None:
        return render_template('error.html', message="No ZIP file has been uploaded yet!")
    res_lst = user_data[user_id]["text_processor"].df.find_common_words()
    return render_template("word count.html", result=res_lst)


@app.route("/select_name")
def select_name():
    user_id = get_user_id()
    options = user_data[user_id]["text_processor"].df.get_names()
    next_action = request.args.get("next_action", "author_sum")  # Default to sum_eng if missing
    return render_template("name options.html", next_action= next_action ,options = options)

@app.route("/select_dates")
def select_dates():
    next_action = request.args.get("next_action", "sum_eng")  # Default to sum_eng if missing
    return render_template("date_time_picker.html", next_action=next_action)

@app.route("/process_dates", methods=["POST"])
def process_dates():
    user_id = get_user_id()
    start_datetime = request.form["start_datetime"]
    end_datetime = request.form["end_datetime"]
    next_action = request.form["next_action"]

    start_dt = parser.parse(start_datetime)
    end_dt = datetime.datetime.now()  # Default to now if no end date is given
    if end_datetime != '':
        end_dt = parser.parse(end_datetime)


    user_data[user_id]["start_date"] = (start_dt.hour, start_dt.minute, start_dt.day, start_dt.month, start_dt.year)
    user_data[user_id]["end_date"] = (end_dt.hour, end_dt.minute, end_dt.day, end_dt.month, end_dt.year)

    return redirect(url_for(next_action))



if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000, debug=False)
    app.run(host="0.0.0.0", port=5001, debug=True)
