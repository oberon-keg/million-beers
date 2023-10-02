"""Insta485 index (main) view."""

import uuid
import hashlib
import pathlib
import flask
import insta485


@insta485.app.route('/accounts/', methods=['POST'])
def account_actions():
    """Display /user route."""
    operation = flask.request.form['operation']
    target = None
    if flask.request.args.get("target"):
        target = flask.request.args['target']

    if operation == 'create':
        fileobj = flask.request.files["file"]
        filename = fileobj.filename
        if len(filename) == 0:
            flask.abort(400)
        # Compute base name (filename without directory).
        # We use a UUID to avoid
        # clashes with existing files, and ensure that the name
        # is compatible with the
        # filesystem.
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix
        uuid_basename = f"{stem}{suffix}"
        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)
        insta485.helpers.create_user(flask.request.form['username'],
                                     flask.request.form['fullname'],
                                     flask.request.form['email'],
                                     uuid_basename,
                                     flask.request.form['password'])

        # log the user in and redirect
        flask.session["username"] = flask.request.form['username']
        target = '/' if target is None else target
        return flask.redirect(target)

    if operation == 'login':
        username = flask.request.form['username']
        pass_in = flask.request.form['password']
        connection = insta485.model.get_db()
        target = '/' if target is None else target
        # empty fields
        if (((username) is None) or ((pass_in) is None)):
            print("empty field")
            flask.abort(400)
        # already logged in
        if 'username' in flask.session:
            return flask.redirect(target)

        pass_db = connection.execute(
            'SELECT * FROM users WHERE username = ?', (
                username,)).fetchone()
        if pass_db is None:
            flask.abort(403)
        else:
            pass_db = pass_db['password']
        # make a list of the stored password string
        split_password = pass_db.split('$')
        # given code:
        algorithm = 'sha512'
        salt = split_password[1]  # [algo, salt, pass]
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + pass_in
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])
        print(password_db_string)
        # made a hashed of the input, check for correctness
        if pass_db != password_db_string:
            print("password incorrect")
            flask.abort(403)

        flask.session['username'] = flask.request.form['username']
        return flask.redirect(target)

    if operation == 'delete':
        username = flask.session['username']
        connection = insta485.model.get_db()
        target = '/' if target is None else target
        configdir = insta485.app.config['UPLOAD_FOLDER']
        # hopefully cascade works
        # delete files, profile first then posts
        profilename = connection.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)).fetchone()['filename']
        profile_path = pathlib.Path.joinpath(configdir, profilename)
        if pathlib.Path.is_file(profile_path):
            profile_path.unlink()
        # deleting posts
        posts = connection.execute(
            'SELECT * FROM posts WHERE owner = ?', (username,)
        )
        for post in posts:
            db_file = post['filename']
            filename = pathlib.Path.joinpath(configdir, db_file)
            if pathlib.Path.is_file(filename):
                filename.unlink()
        # rmv from tables
        connection.execute('DELETE FROM users WHERE username = ?', (username,))
        flask.session.clear()
        return flask.redirect(target)

    if operation == 'edit_account':
        username = flask.session["username"]
        connection = insta485.model.get_db()
        fullname = flask.request.form['fullname']
        email = flask.request.form['email']
        configdir = insta485.app.config['UPLOAD_FOLDER']
        target = '/' if target is None else target
        if ((len(fullname) == 0) or (len(email) == 0)):
            flask.abort(400)
        # Unpack flask object
        fileobj = flask.request.files["file"]
        filename = fileobj.filename
        if filename != '':  # FILE exists
            # Compute base name (filename without directory).
            # We use a UUID to avoid
            # clashes with existing files, and ensure
            # that the name is compatible with the
            # filesystem.
            stem = uuid.uuid4().hex
            suffix = pathlib.Path(filename).suffix
            uuid_basename = f"{stem}{suffix}"
            # Save to disk
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
            fileobj.save(path)
            # FILE SAVED
            # NOW DELETE OLD FILE
            filename_old = connection.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()['filename']
            old_path = pathlib.Path.joinpath(configdir, filename_old)
            old_path.unlink()
            # now update with new path
            connection.execute(
                'UPDATE users SET filename = ? WHERE username = ?',
                (uuid_basename, username)
            )  # ok done saving, do the others outside of if
        # updating email and fullname
        connection.execute(
            'UPDATE users SET email = ? WHERE username = ?',
            (email, username)
        )
        connection.execute(
            'UPDATE users SET fullname = ? WHERE username = ?',
            (fullname, username)
        )
        return flask.redirect(target)

    if operation == 'update_password':
        logname = flask.session["username"]
        connection = insta485.model.get_db()
        # check for empty fields
        password_given = flask.request.form['password']
        new_pass1 = flask.request.form['new_password1']
        new_pass2 = flask.request.form['new_password2']
        if ((len(password_given) == 0) or
           (len(new_pass1) == 0) or
           (len(new_pass2) == 0)):

            print("empty field")
            flask.abort(400)
        # updating password,its either this or a GET
        pass_db = connection.execute(
            'SELECT * FROM users WHERE username = ?', (
                logname,)).fetchone()['password']
        # make a list of the stored password string
        split_password = pass_db.split('$')
        # given code:
        algorithm = 'sha512'
        salt = split_password[1]
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password_given
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])
        print(password_db_string)
        # made a hashed of the input, check for correctness
        if pass_db != password_db_string:
            print("Old password incorrect")
            flask.abort(403)
        if new_pass1 != new_pass2:
            print("passwords do not match")
            flask.abort(401)
        # update db
        algorithm = 'sha512'
        salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + new_pass1
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])
        connection.execute(
            'UPDATE users SET password = ? WHERE username = ?',
            (password_db_string, logname))
        target = '/' if target is None else target
        return flask.redirect(target)


@insta485.app.route('/accounts/login/', methods=['GET'])
def show_login():
    """Display /user route."""
    if 'username' in flask.session:
        return flask.redirect("/", code=302)

    return flask.render_template("login.html")


@insta485.app.route('/accounts/logout/', methods=['POST'])
def user_logout():
    """User logout."""
    flask.session["username"] = ''
    flask.session.clear()
    return flask.redirect('/accounts/login/')


@insta485.app.route('/accounts/create/')
def show_create():
    """Display /user route."""
    if 'username' in flask.session:
        return flask.redirect("/accounts/edit", code=302)

    return flask.render_template("create.html")


@insta485.app.route('/accounts/delete/')
def show_delete():
    """Display delete page."""
    logname = flask.session["username"]
    context = {"username": logname}
    return flask.render_template("delete.html", **context)


@insta485.app.route('/accounts/edit/')
def show_edit():
    """Display /user route."""
    logname = flask.session["username"]
    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT filename, fullname, email "
        "FROM users "
        "WHERE username = ?",
        (logname, )
    )

    temp = cur.fetchall()
    if len(temp) == 0:
        print("Error 404: user to edit was not found")
        flask.abort(404)

    temp = temp[0]

    image = temp["filename"]
    fullname = temp["fullname"]
    email = temp["email"]
    image = \
        flask.url_for("download_file", filename=image)
    print(image)

    context = {
        "username": logname,
        "fullname": fullname,
        "email": email,
        "image": image,
        "current_url": flask.request.path
    }

    return flask.render_template("edit.html", **context)


@insta485.app.route('/accounts/password/', methods=['GET'])
def show_password():
    """Show password."""
    return flask.render_template('/password.html')
