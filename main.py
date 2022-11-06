from flask import Flask, render_template, url_for, request, flash, session, redirect, send_file
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
from time import sleep
from random import shuffle
from io import TextIOWrapper
from config import DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT
import cli

#from flaskext.noextref import NoExtRef

app = Flask(__name__)
app.secret_key = 'mi-ne-pendosi'

# DB_NAME = 'words'
# DB_USER = 'admin'
# DB_PASS = 'admin'
# # DB_HOST = 'localhost'
#DB_URL = 'postgres://cssuehtndgmavj:4a96332271add397fcf4ede36bbb3fa94a77ab2329f78c4f051d2c5ac306fd58@ec2-54-91-223-99.compute-1.amazonaws.com:5432/d18idpvuarqsho'


def create_db():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(cli.create_database())

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    create_db()
except:
    print('no conn')


@app.route('/')
def home():
    # Check if user is loggedin
    #session.permanent = True
    print(session)
    if 'loggedin' in session:
        session['word_id'] = 0 #in place where we know or don't know new word
        # User is loggedin show them the home page
        return render_template('home.html', username=session['user_name'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        user_login = request.form['username']
        password = request.form['password']
        print(password)

        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM user_db WHERE user_login = %s', (user_login,))
        # Fetch one record and return result
        account = cursor.fetchone()

        if account:
            password_rs = account['user_password']
            print(password_rs)
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['user_login'] = account['user_login']
                session['user_name'] = account['user_name']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
        # Show registration form with message (if any)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        user_login = request.form['username']
        password = request.form['password']
        _hashed_password = generate_password_hash(password)
        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM user_db WHERE user_login = %s', (user_login,))
        account = cursor.fetchone()
        print('ff')
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        elif not re.match(r'[A-Za-z0-9]+', user_login):
            flash('Username must contain only characters and numbers!')
        elif not user_login or not password or not fullname:
            flash('Please fill out the form!')
        else:
            # Account don't exist and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO user_db (user_login, user_password, user_name) VALUES (%s,%s,%s)",
                           (user_login, _hashed_password, fullname))
            conn.commit()

            return redirect(url_for('login'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
        # Show registration form with message (if any)

    return render_template('register.html')


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.clear()
    return redirect(url_for('login'))


@app.route('/createlist', methods=['GET', 'POST'])
def create_list():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        if request.method == 'POST':
            name_list = request.form['name_list']

            if not re.match(r'[A-Za-z0-9]+', name_list):
                flash('must contain only characters and numbers!', category='error')
            elif not name_list:
                flash('Please fill out the form!', category='error')
            elif (len(name_list) > 30):
                flash('Max length is 30!', category='error')
            else:
                # Account don't exist and the form data is valid, now insert new account into users table
                cursor.execute("INSERT INTO word_list (name_list, user_login) VALUES (%s,%s)",
                               (name_list, session['user_login']))
                conn.commit()
                flash('List created!', category='success')

                return redirect(url_for('userlists'))

        elif request.method == 'POST':
            # Form is empty... (no POST data)
            flash('Please fill out the form!')

        return render_template('createlist.html')

    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM user_db WHERE user_login = %s', [session['user_login']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/userlists')
def userlists():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT id_list, name_list, is_public FROM word_list WHERE user_login = %s', [session['user_login']])
        account = cursor.fetchall()
        cursor.execute('SELECT name_list, id_list FROM user_added_list JOIN word_list USING (id_list) WHERE user_added_list.user_login = %s', [session['user_login']])
        added_lists = cursor.fetchall()
        return render_template('user_lists.html', account=account, added_lists=added_lists)
    return redirect(url_for('login'))


@app.route('/userwords/<int:id>', methods=['GET']) #Flask-NoExtRef to hide URL
def userwords(id):
    if 'loggedin' in session:
        session['id_list'] = id
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT word_id, word_name, word_translation FROM word WHERE id_list = %s', [id])
        account = cursor.fetchall()
        return render_template('userwords.html', account=account)
    return redirect(url_for('login'))


@app.route('/publicwords/<int:id>', methods=['GET', 'POST'])
def otheruserwords(id):
    if 'loggedin' in session:
        session['id_list'] = id
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT word_id, word_name, word_translation FROM word WHERE id_list = %s', [id])
        account = cursor.fetchall()

        if request.method == 'POST': #submit rating
            rating = request.form['rating']
            print(rating)
            if rating == 'Submit':
                flash('Choose a rating!', category='error')
            else:
                cursor.execute("SELECT EXISTS (SELECT * FROM list_rating WHERE id_list = %s AND user_login = %s)", (id, session['user_login']))
                alreadyrated = cursor.fetchone()
                print(alreadyrated)
                if alreadyrated[0]:
                    flash('Looks like you have rated this list!', category='error')
                else:
                    cursor.execute(
                    "INSERT INTO list_rating (rating_value, id_list, user_login) VALUES (%s, %s, %s) ",
                    (rating, id, session['user_login']))
                    conn.commit()
                    flash('Thanks :)', category='success')
        return render_template('otheruserwords.html', account=account)
    return redirect(url_for('login'))


@app.route('/userexamples/<int:id>', methods=['GET'])
def userexamples(id):
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT word_example_id, usage_example, example_translation FROM word_usage WHERE word_id = %s', [id])
        account = cursor.fetchall()
        return render_template('userexamples.html', account=account)
    return redirect(url_for('login'))


@app.route('/creating', methods=['GET', 'POST'])
def createwordandexamples():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        if request.method == 'POST':
            word_name = request.form['word_name']
            word_translation = request.form['word_translation']
            example_translation = request.form.getlist('caseextrans[]')
            example_name = request.form.getlist('caseex[]')
            if not word_name or not word_translation:
                flash('Please fill out all forms!', category='error')
            elif len(word_name) > 30 :
                flash('Max length of word is 30', category='error')
            elif len(word_translation) > 60:
                flash('Max length of translation is 60', category='error')
            else:
                cursor.execute(
                    "INSERT INTO word (word_name, word_translation, id_list) VALUES (%s,%s,%s) RETURNING word_id",
                               (word_name, word_translation, session['id_list']))
                conn.commit()
                word_id = cursor.fetchone()[0]
                if example_translation or example_name:
                    for i in range(len(example_name)):
                        cursor.execute(
                            "INSERT INTO word_usage (usage_example, example_translation, word_id) VALUES (%s,%s,%s)",
                            (example_name[i], example_translation[i], word_id))
                        conn.commit()

                cursor.execute(
                    "INSERT INTO word_learning (stage, date_gain_stage, user_login, word_id) VALUES (%s,LOCALTIMESTAMP,%s,%s)",
                    (0, session['user_login'], word_id))

                conn.commit()

                flash('Word created!', category='success')
                return redirect(url_for('userwords', id=session['id_list']))

        return render_template('create_word_and_examples.html')

    return redirect(url_for('login'))


@app.route('/listsfromotherusers', methods=['GET', 'POST'])
def lists_from_users():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:

        cursor.execute('SELECT id_list, name_list, user_login FROM word_list WHERE is_public = True ')
        account = cursor.fetchall()

        cursor.execute('SELECT id_list FROM user_added_list WHERE user_login = %s', [session['user_login']])
        user_added_lists = cursor.fetchall()

        #если будет долго, можно за один проход по аккаунту сделать, объединить с нижним
        isuser_list = [i[2] in ([session['user_login']]) or i[0] in (j[0] for j in user_added_lists) for i in account]


        cursor.execute('SELECT id_list, COUNT(user_login) as user_quantity, SUM(rating_value)/COUNT(user_login) as rating FROM list_rating GROUP BY id_list HAVING COUNT(user_login) >= 1')
        lists_rating_from_table = cursor.fetchall()

        lists_rating = []
        for i in account:
            i_in_j = False
            for j in lists_rating_from_table:
                if i[0] == j[0]:
                    i_in_j = True
                    lists_rating.append([round(j[2], 3), j[1]])
                    break
            if not i_in_j:
                lists_rating.append(["Not yet rated", 'Nobody'])

        return render_template('lists_from_users.html', account=account, isuser_list=isuser_list, lists_rating=lists_rating)
    return redirect(url_for('login'))


@app.route('/makingpublic/<int:id>', methods=['GET', 'POST']) #юрл никогда не видно, промежуточная функция
def makelistpublic(id):
    if request.method == 'POST':
        if (request.form.get('yes', None)):
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(
                "UPDATE word_list SET is_public = 'True' WHERE id_list = %s",
                [id])
            conn.commit()
            return redirect(url_for('lists_from_users'))
        else:
            return redirect(url_for('userlists'))
    return render_template('delete_list.html')


@app.route('/renamelist/<int:id>', methods=['GET', 'POST'])
def renamelist(id):
    if request.method == 'POST':
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        name = request.form['newname']
        cursor.execute(
            "UPDATE word_list SET name_list = %s WHERE id_list = %s",
            (name, [id][0]))
        conn.commit()
        return redirect(url_for('userlists'))
    return render_template('rename_list.html')


@app.route('/deletelist/<int:id>', methods=['GET', 'POST'])
def deletelist(id):
    if request.method == 'POST':
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if (request.form.get('yes', None)):
            cursor.execute(
                "SELECT user_login FROM user_added_list WHERE id_list = %s",
                [id])
            whose_list = cursor.fetchone()
            print(whose_list, session['user_login'])

            cursor.execute(
                "SELECT word_id FROM word WHERE id_list = %s",
                [id])
            words_to_delete = cursor.fetchall()

            if whose_list is not None:
                cursor.execute(
                    "DELETE FROM user_added_list WHERE id_list = %s",
                    [id])
                conn.commit()
            else:
                for word_id in words_to_delete:
                    cursor.execute(
                        "DELETE FROM word_usage WHERE word_id = %s",
                        [word_id[0]])
                    conn.commit()

                cursor.execute(
                    "DELETE FROM word WHERE id_list = %s",
                    [id])
                conn.commit()
                cursor.execute(
                    "DELETE FROM word_list WHERE id_list = %s",
                    [id])
                conn.commit()

            for word_id in words_to_delete:
                cursor.execute(
                    "DELETE FROM word_learning WHERE word_id = %s",
                    [word_id[0]])
                conn.commit()


        return redirect(url_for('userlists'))
    return render_template('delete_list.html')


@app.route('/deleteword/<int:id>', methods=['GET', 'POST'])
def deleteword(id):
    if request.method == 'POST':
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if (request.form.get('yes', None)):
            cursor.execute(
                "DELETE FROM word_learning WHERE word_id = %s",
                [id])
            conn.commit()
            cursor.execute(
                "DELETE FROM word_usage WHERE word_id = %s",
                [id])
            conn.commit()
            cursor.execute(
                "DELETE FROM word WHERE word_id = %s",
                [id])
            conn.commit()
            return redirect(url_for('userwords', id=session['id_list']))
    return render_template('delete_list.html')


@app.route('/editword/<int:id>', methods=['GET', 'POST'])
def editword(id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT usage_example, example_translation FROM word_usage WHERE word_id = %s',
                   [id])
    word_examples = cursor.fetchall()
    cursor.execute('SELECT word_name, word_translation FROM word WHERE word_id = %s',
                   [id])
    word_info = cursor.fetchall()[0]
    print(id)
    if request.method == 'POST':
        word_name = request.form['word_name']
        word_translation = request.form['word_translation']
        example_translation = request.form.getlist('caseextrans[]')
        example_name = request.form.getlist('caseex[]')
        print(word_name)
        if not word_name or not word_translation:
            flash('Please fill out all forms!', category='error')
        elif len(word_name) > 30:
            flash('Max length of word is 30', category='error')
        elif len(word_translation) > 60:
            flash('Max length of translation is 60', category='error')
        else:
            cursor.execute(
                "UPDATE word SET word_name = %s, word_translation = %s WHERE word_id = %s",
                (word_name, word_translation, id))
            conn.commit()
            if example_translation or example_name:
                for i in range(len(example_name)):
                    cursor.execute(
                        "UPDATE word_usage SET usage_example = %s, example_translation = %s WHERE word_id = %s",
                        (example_name[i], example_translation[i], id))
                    conn.commit()

            flash('Word edited!', category='success')
            return redirect(url_for('userwords', id=session['id_list']))

    return render_template('edit_word.html', example=word_examples, word=word_info)


@app.route('/adding', methods=['GET', 'POST']) #юрл никогда не видно, промежуточная функция
def addlist():
    id = request.args.get('id', None)
    list_id = [id][0]
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute(
            "INSERT INTO user_added_list (id_list, user_login) VALUES (%s,%s)",
            (list_id, session['user_login']))
        conn.commit()

        cursor.execute(
            "SELECT word_id FROM word WHERE id_list = %s",
            ([list_id]))
        words_in_new_list = cursor.fetchall()

        for word_id in words_in_new_list:
            cursor.execute(
                "INSERT INTO word_learning (stage, date_gain_stage, user_login, word_id) VALUES (%s,LOCALTIMESTAMP,%s,%s)",
                (0, session['user_login'], word_id[0]))
            conn.commit()

        return redirect(url_for('userlists'))

    return redirect(url_for('login'))


@app.route('/new_word', methods=['GET', 'POST'])
def word_learning():
    if 'loggedin' in session:
        words_to_repetition = istimetorepetition()
        if words_to_repetition:
            words_usage, repetion_result = [], []
            number_of_words = len(words_to_repetition)
            for i in range(number_of_words):
                word_to_learn_id = words_to_repetition[i][2]
                words_to_repetition[i] += get_word_info(word_to_learn_id)
                words_usage.append(get_word_examples(word_to_learn_id))
                repetion_result.append([word_to_learn_id, 0])
            session['words_to_learn'] = words_to_repetition
            session['words_usage'] = words_usage
            session['current_word'] = 0
            session['number_of_words'] = number_of_words
            session['attempts'] = 3
            session['repition_result'] = repetion_result
            session['previous_answer'] = ''
            return redirect(url_for('repetitionwords'))
        else:
            words_to_memorize = istimetomemorize()
            if words_to_memorize:
                words_usage = []
                for i in range(5):
                    word_to_learn_id = words_to_memorize[i][2]
                    words_to_memorize[i] += get_word_info(word_to_learn_id)
                    words_usage.append(get_word_examples(word_to_learn_id))
                session['words_to_learn'] = words_to_memorize
                session['words_usage'] = words_usage
                session['current_word'] = 0
                return redirect(url_for('memorizewords'))
            else:
                if request.method == 'GET':
                    if session['word_id'] == 0:  # если этого велосипеда не сделать, то при отправке пост запроса будут
                                                                    #заноситься следующие сгенерированные данные
                        session['word'], session['word_usage'], session['word_id'] = new_learning_word()

                if request.method == 'POST':
                    if (request.form.get('starlearning', None)):
                        firststage(session['word_id'])

                    elif (request.form.get('alreadylearned', None)):
                        alreadylearned(session['word_id'])
                    else:
                        pass
                    session['word_id'] = 0

                    words_to_memorize = istimetomemorize()
                    if words_to_memorize:
                        return redirect(url_for('word_learning'))

                    session['word'], session['word_usage'], session['word_id'] = new_learning_word()

        return render_template('wordlearning.html', word=session['word'], word_usage=session['word_usage'])
    return redirect(url_for('login'))


@app.route('/repetition', methods=['GET', 'POST'])
def repetitionwords():
    i = session['current_word']
    remain = session['number_of_words']
    if request.method == 'POST':
        if (request.form.get('not', None)):
            session['attempts'] = 3
            session['number_of_words'] -= 1
            session['current_word'] += 1
            return render_template('repetition_hint.html', word=session['words_to_learn'][i],
                                   word_ex=session['words_usage'][i], remain=remain)
        elif (request.form.get('answer', None)):
            answer = request.form.get('answer').lower()
            if session['previous_answer'] == answer:
                flash('''Select another answer or
                                              don't reload the page''', category='error')
            else:
                session['previous_answer'] = answer
                j = session['current_word']
                print(session['words_to_learn'][j])
                print('gfgd')
                if answer == session['words_to_learn'][j][3].lower():
                    flash("correct", category="success")
                    sleep(0.3)
                    session['attempts'] = 3
                    session['repition_result'][j][1] = 1
                    session['current_word'] += 1
                    session['number_of_words'] -= 1
                else:
                    session['attempts'] -= 1
                    flash("incorrect", category="error")
                    if session['attempts'] == 0:
                        sleep(0.3)
                        session['attempts'] = 3
                        session['current_word'] += 1
                        session['number_of_words'] -= 1
                        return render_template('repetition_hint.html', word=session['words_to_learn'][i],
                                               word_ex=session['words_usage'][i], remain=remain)

        print(session['number_of_words'])
    if session['number_of_words'] == 0:
        repetitionresults()
        return redirect(url_for('word_learning'))

    i = session['current_word']
    remain = session['number_of_words']
    attempts = session['attempts']
    print(session['repition_result'])
    return render_template('word_repetition.html', word=session['words_to_learn'][i][4], word_ex=session['words_usage'][i], remain=remain, attempt=attempts)


@app.route('/memorizing', methods=['GET', 'POST'])
def memorizewords():
    if request.method == 'POST':
        if (request.form.get('nextword', None)):
            session['current_word'] += 1
            if session['current_word'] == 5:

                our_translations, our_words, word_and_translation = [], [], []
                for word in session['words_to_learn']:
                    word_and_translation.append([word[3], word[4], 0, word[2]]) #name, translation, completetask, id
                    our_translations.append([word[4]])
                    our_words.append([word[3]])

                session['current_word'] = 0
                session['our_translations'] = our_translations #[[рука]]
                session['our_words'] = our_words #[[hand]]
                shuffle(our_translations)
                shuffle(word_and_translation)
                shuffle(our_words)
                session['our_words_translations'] = word_and_translation #[[hand, рука, 0]]
                session['attempts'] = 3
                session['previous_answer'] = ''  # prevent decreasing attempt on reloading
                session['isresults'] = session['istask2'] = session['istask3'] = False # prevent from reloading
                return redirect(url_for('select_translation'))

        elif (request.form.get('previousword', None)):
            session['current_word'] -= 1
        else:
            pass

    i = session['current_word']
    return render_template('word_card.html', word=session['words_to_learn'][i], word_ex=session['words_usage'][i], index_word=i)



@app.route('/task1', methods=['GET', 'POST'])
def select_translation():
    if session['istask2']:
        return redirect(url_for('memorizewords'))

    words = session['our_words_translations']
    if request.method == 'POST':
            answer = request.form.get('answer').lower()
            if session['previous_answer'] == answer:
                flash('''Select another answer or
                                  don't reload the page''', category='error')
            else:
                session['previous_answer'] = answer
                j = session['current_word']
                if answer == words[j][1].lower():
                    flash("correct", category="success")
                    sleep(0.3)
                    session['attempts'] = 3
                    session['our_words_translations'][j][2] += 1
                    session['current_word'] += 1
                else:
                    session['attempts'] -= 1
                    flash("incorrect", category="error")
                    if session['attempts'] == 0:
                        sleep(0.3)
                        session['attempts'] = 3
                        session['current_word'] += 1

                if session['current_word'] == 5:
                    session['attempts'] = 3
                    session['current_word'] = 0
                    session['previous_answer'] = ''
                    return redirect(url_for('select_word'))


    translations = random_translations()
    translations += session['our_translations']
    shuffle(translations)
    attempt = session['attempts']
    i = session['current_word']
    return render_template('word_task1.html', word=words[i], translations=translations, index_word=i, attempt=attempt)


@app.route('/task2', methods=['GET', 'POST'])
def select_word():
    session['istask2'] = True
    if session['istask3']:
        return redirect(url_for('memorizewords'))

    j = session['current_word']
    words = session['our_words_translations']

    if request.method == 'POST' and 'word' in request.form:
        answer = request.form.get('word').lower()
        if session['previous_answer'] == answer:
            flash('''Write another answer or
                  don't reload the page''', category='error')
        else:
            session['previous_answer'] = answer
            if answer == words[j][0].lower():
                flash("correct", category="success")
                sleep(0.1)
                session['attempts'] = 3
                session['our_words_translations'][j][2] += 1
                session['current_word'] += 1
            else:
                flash("incorrect", category="error")
                sleep(0.1)
                session['attempts'] -= 1
                if session['attempts'] == 0:
                    sleep(1)
                    session['attempts'] = 3
                    session['current_word'] += 1

            if session['current_word'] == 5:
                session['attempts'] = 3
                session['current_word'] = 0
                session['previous_click'] = ''
                codes = [0, 1, 2, 3, 4]
                shuffle(codes)
                session['numbers'] = codes
                session['task_results'] = []
                return redirect(url_for('matching'))

    attempt = session['attempts']
    i = session['current_word']
    return render_template('word_task2.html', word=words[i], attempt=attempt)


@app.route('/task3', methods=['GET', 'POST'])
def matching():
    session['istask3'] = True
    if session['isresults']:
        return redirect(url_for('memorizewords'))

    numbers = session['numbers']

    if request.method == 'POST':
        for i in range(10):
            if (request.form.get(f'{i}')):
                answer_ind = i
                clc = session['previous_click']
                if clc != '':
                    if clc > 4:                              #word
                        if answer_ind > 4:
                            flash('Other column! Try again!', category='error')
                            break
                        else:
                            clc -= 5
                    else:                                    #translation
                        if answer_ind < 5:
                            flash('Other column! Try again!', category='error')
                            break
                        else:
                            answer_ind -= 5

                    if clc == answer_ind:
                        print(clc, answer_ind)
                        session['our_words_translations'][clc][2] += 1
                        session['task_results'].append(session['our_words_translations'].pop(clc))
                        print(session['task_results'])
                        numbers.remove(max(numbers))
                        flash('Correct!', category='success')
                    else:
                        flash('Fail!', category='error')
                        session['attempts'] -= 1

                    session['previous_click'] = ''
                    shuffle(numbers)
                    session['numbers'] = numbers

                else:
                    session['previous_click'] = answer_ind
                break

    if not numbers or session['attempts'] == 0:
        for word in session['our_words_translations']:
            session['task_results'].append(word)
        sleep(0.3)
        return redirect(url_for('task_results'))

    words = session['our_words_translations']
    attempt = session['attempts']

    return render_template('word_task3.html', words=words, ind=numbers, attempt=attempt)


@app.route('/results', methods=['GET', 'POST'])
def task_results():
    if not session['isresults']: #prevent from reloading
        session['isresults'] = True
        task_results = session['task_results']
        session['word_stages'], session['learned_word'] = [], []
        for task_result in task_results:
            completed_task = task_result[2]
            word_id = task_result[3]
            word_stage = new_word_stage_memorize(completed_task, word_id)
            session['word_stages'].append(word_stage)
            session['learned_word'].append(task_result[0])
        return render_template('taskresults.html', word_stages=session['word_stages'],
                                   words=session['learned_word'])
    else:
        return redirect(url_for('memorizewords'))


@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        file = request.files['file'] #io.BytesIO format
        if file:
            try:
                data = TextIOWrapper(file, encoding='utf-8')
                add_words_from_file(data)
            except:
                flash('Only symbols! txt format or so', category='error')
        else:
            flash('Choose file!', category='error')

    return render_template('download_from_file.html')


def add_words_from_file(data):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    lines = data.readlines()
    word_name = ''
    for line in lines:
        line = line.strip()
        if line not in ['RU', 'EN']:
            if re.match(r'[A-Za-z0-9\s]+', line) and len(line) < 61:
                word_name = line
            elif re.match(r'[0-9А-Яа-я\s]+', line) and len(line) < 61:
                word_translation = line
                if word_name != '':
                    cursor.execute(
                        "INSERT INTO word (word_name, word_translation, id_list) VALUES (%s,%s,%s) RETURNING word_id",
                        (word_name, word_translation, session['id_list']))
                    conn.commit()
                    word_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO word_learning (stage, date_gain_stage, user_login, word_id) VALUES (%s,LOCALTIMESTAMP,%s,%s)",
                        (0, session['user_login'], word_id))
                    conn.commit()
                    word_name = ''
            else:
                word_name = ''


def repetitionresults():
    task_results = session['repition_result']
    for task_result in task_results:
        completed_task = task_result[1]
        word_id = task_result[0]
        new_word_stage_repetition(completed_task, word_id)


def new_word_stage_repetition(completed_task, word_id):
    if completed_task not in [0, 1]:
        flash(completed_task, category='error')
        current_stage = 'Error! No data'
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        new_stage = [-1, 2][completed_task == 1]

        cursor.execute(
            "UPDATE word_learning SET stage = stage + %s, date_gain_stage = LOCALTIMESTAMP WHERE word_id = %s "
            "AND user_login = %s RETURNING stage ",
            (new_stage, word_id, session['user_login']))
        current_stage = cursor.fetchone()
        conn.commit()


def new_word_stage_memorize(completed_task, word_id):
    if completed_task not in [0, 1, 2, 3]:
        flash(completed_task, category='error')
        new_stage = 'Error! No data'
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        new_stage = [-1, 1][completed_task == 3]
        cursor.execute(
            "SELECT stage FROM word_learning WHERE word_id = %s AND user_login = %s",
            (word_id, session['user_login']))
        old_stage = cursor.fetchone()[0]

        if new_stage == -1:
            if old_stage != 1:
                cursor.execute(
                    "UPDATE word_learning SET stage = stage + %s, date_gain_stage = LOCALTIMESTAMP WHERE word_id = %s AND user_login = %s",
                    (new_stage,  word_id, session['user_login']))
                conn.commit()
                new_stage = 'has decreased to: ' + str(old_stage - 1)
            else:
                new_stage = "hasn't changed"
        else:
            if old_stage == 1:
                new_stage = old_stage = 2

            cursor.execute(
                "UPDATE word_learning SET stage = stage + %s, date_gain_stage = LOCALTIMESTAMP WHERE word_id = %s AND user_login = %s",
                (new_stage, word_id, session['user_login']))
            conn.commit()
            new_stage = 'increased to: ' + str(old_stage + 1)

    return new_stage



def random_translations():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT word_translation FROM word ORDER BY RANDOM() LIMIT 10")
    translations = cursor.fetchall()
    if len(translations) < 10:
        translations = [['Стойка регистрации'], ['Инфляция'], ['Конформизм'], ['Сон'], ['Отако'],
                        ['Клептомания'], ['Меланхолия'], ['Смысл'], ['Эпатаж'], ['Аллюзия']]
    return translations


def istimetomemorize(): #выдаем 5 слов для изучения подходящей стадии если они есть (пока не проверяю время)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT stage, date_gain_stage, word_id FROM  word_learning WHERE user_login = %s"
                   " AND ((stage = 1) "
                   "OR (stage = 2) "
                   "OR (stage = 4)"
                   "OR (stage = 6)"
                   "OR (stage = 8)"
                   "OR (stage = 10) )"
                   "ORDER BY RANDOM()", session['user_login'])

    words_to_learn = cursor.fetchall()

    if len(words_to_learn) % 5 != 0:
        words_to_learn = []
    return words_to_learn[:5] #first five


def istimetorepetition(): #выдаем 5 слов для изучения подходящей стадии если они есть (пока не проверяю время)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT stage, date_gain_stage, word_id FROM  word_learning WHERE user_login = %s"
                   " AND (stage, date_gain_stage) IN (SELECT stage, date_gain_stage FROM word_learning "
                   "WHERE "
                   " (stage = 3 AND LOCALTIMESTAMP - INTERVAL '3 HOURS' > date_gain_stage) " #0 MINUTES
                   "OR (stage = 5 AND LOCALTIMESTAMP - INTERVAL '1 DAY' > date_gain_stage)" # 
                   "OR (stage = 7 AND LOCALTIMESTAMP - INTERVAL '3 DAYS' > date_gain_stage)" # 
                   "OR (stage = 9 AND LOCALTIMESTAMP - INTERVAL '7 DAYS' > date_gain_stage)" #
                   "OR (stage = 11 AND LOCALTIMESTAMP - INTERVAL '30 DAYS' > date_gain_stage)) " #
                   "ORDER BY RANDOM()", session['user_login'])

    words_to_learn = cursor.fetchall()
    return words_to_learn


def new_learning_word():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "SELECT stage, date_gain_stage, word_id FROM  word_learning WHERE stage = 0 AND user_login = %s ORDER BY RANDOM() LIMIT 1 ", session['user_login'])

    random_word = cursor.fetchone()
    if not random_word:
        random_word=['All words are learned', '-', 0]

    print(random_word)
    word_id = random_word[2]
    word_info = get_word_info(word_id)
    print(word_info)
    word_usage = get_word_examples(word_id)
    word = random_word + word_info
    print(word)
    return word, word_usage, word_id


def get_word_info(word_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "SELECT word_name, word_translation FROM word WHERE word_id = %s ", [word_id])
    word_info = cursor.fetchone()
    if not word_info:
        word_info = ['Add or create new collections', 'Have a nice day :)']
    return word_info


def get_word_examples(word_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "SELECT usage_example, example_translation FROM word_usage WHERE word_id = %s ", [word_id])

    word_usage = cursor.fetchall()
    if not word_usage:
        word_usage = [['No examples', 'No examples']]
    return word_usage


def alreadylearned(word_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "UPDATE word_learning SET stage = %s, date_gain_stage = LOCALTIMESTAMP WHERE word_id = %s AND user_login = %s",
        (13, word_id, session['user_login']))
    conn.commit()


def firststage(word_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "UPDATE word_learning SET stage = %s, date_gain_stage = LOCALTIMESTAMP WHERE word_id = %s AND user_login = %s",
        (1, word_id, session['user_login']))
    conn.commit()


@app.route('/win', methods=['GET', 'POST'])
def kursovaya_win():
    return render_template('kursovaya_win.html')


if __name__ == "__main__":
    app.run(debug=True)



