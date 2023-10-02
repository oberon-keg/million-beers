"""
Insta485 index (main) view.

URLs include:
/
"""

from crypt import methods
from operator import methodcaller
import flask
import arrow
import uuid
import pathlib
import os
import insta485
import insta485.helpers


@insta485.app.route('/')
def show_index():
    """Display / route."""
    # Connect to database
    connection = insta485.model.get_db()
    """ Requirement for All Pages """
    # Check for logname defined
    if "username" not in flask.session or not len(flask.session["username"]):
        return flask.redirect('/accounts/login/')

    user = flask.session["username"]

    """" Query Database """

    posts = connection.execute(
        "WITH users_following AS ("
        "    SELECT username2"
        "    FROM following"
        "    WHERE username1='{}'"
        "    UNION ALL SELECT '{}'"
        " ) "
        "SELECT "
        " DISTINCT(postid)"  # Distinct handles repeats in alias table
        ", posts.filename AS image"
        ", owner"
        ", posts.created"
        ", users.filename AS owner_image"
        " FROM posts"
        " LEFT JOIN users"
        " ON owner = users.username"
        " JOIN users_following"
        " ON owner=users_following.username2"
        " ORDER BY posts.postid DESC".format(user, user)
    ).fetchall()

    for post in posts:
        post["image"] = flask.url_for("download_file", filename=post["image"])
        post["owner_image"] = flask.url_for("download_file",
                                            filename=post["owner_image"])
        time = arrow.get(post["created"])
        post["created"] = time.humanize()

        # like info tracks:
        # -- number of likes
        # -- Boolean if logged in user likes post
        post["like_info"] = connection.execute(
            " SELECT"
            " SUM(CASE WHEN owner == '{}' THEN 1 ELSE 0 END)"
            " AS liked_by_logname"  # track if logname likes post
            ", COUNT(*) AS like_count"
            " FROM likes"
            " WHERE"
            " postid = {}".format(user, post["postid"])
        ).fetchall()[0]

        # Faster to assign comments to posts through SQL calls than Python
        post["comments"] = connection.execute(
            "SELECT "
            "owner"
            ", postid"
            ", text"
            ", created"
            " FROM comments"
            " WHERE postid = {} ".format(post["postid"])
        ).fetchall()

    # Add database info to context
    context = {
        "logname": user,
        "posts": posts,
        "current_url": flask.request.path
    }

    return flask.render_template("index.html", **context)


@insta485.app.route('/login/', methods=['POST'])
def login():
    """Form login."""
    print("DEBUG Login: ", flask.request.form['username'])
    flask.session['username'] = flask.request.form['username']
    return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/likes/', methods=['POST'])
def likes():
    """Handle likes."""
    # Check for logname defined
    if "username" not in flask.session or not len(flask.session["username"]):
        return flask.redirect('/accounts/login/')

    user = flask.session["username"]
    operation = flask.request.form['operation']
    postid = flask.request.form['postid']

    if operation == 'like':
        insta485.helpers.add_like(user, postid)
    else:
        insta485.helpers.delete_like(user, postid)

    if 'target' not in flask.request.args:
        target = '/'
    else:
        target = flask.request.args['target']
    return flask.redirect(target)


@insta485.app.route('/comments/', methods=['POST'])
def comments():
    """Handle comments."""
    # Check for logname defined
    if "username" not in flask.session:
        # insta485.app.logger.debug("Set logname=%s", logname)
        return """
        <form action="/login/" method="post">
        <p><input type="text" name="username"></p>
        <p><input type="submit" value="Login"></p>
        </form>
        """

    user = flask.session["username"]
    operation = flask.request.form['operation']

    if operation == 'create':
        postid = flask.request.form['postid']
        text = flask.request.form['text']
        if len(text) == 0:
            # empty comment
            flask.abort(400)
        insta485.helpers.add_comment(user, postid, text)

    elif operation == 'delete':
        commentid = flask.request.form['commentid']
        insta485.helpers.delete_comment(user, commentid)

    if 'target' not in flask.request.args:
        target = '/'
    else:
        target = flask.request.args['target']

    return flask.redirect(target)


@insta485.app.route('/following/', methods=['POST'])
def following():
    """Determine following."""
    # Check for logname defined
    if "username" not in flask.session or not len(flask.session["username"]):
        return flask.redirect('/accounts/login/')

    user = flask.session["username"]
    operation = flask.request.form['operation']
    recipient = flask.request.form['username']

    if operation == 'follow':
        insta485.helpers.add_follow(user, recipient)

    elif operation == 'unfollow':
        insta485.helpers.remove_follow(user, recipient)

    if 'target' not in flask.request.args:
        target = '/'
    else:
        target = flask.request.args['target']
    return flask.redirect(target)


@insta485.app.route('/posts/<postid>/', methods=['GET'])
def show_post(postid):
    """Show post by postid."""
    # Connect to database
    connection = insta485.model.get_db()
    """ Requirement for All Pages """
    # Check for logname defined
    if "username" not in flask.session or not len(flask.session["username"]):
        return flask.redirect('/accounts/login/')

    user = flask.session["username"]
    post = connection.execute(
        "SELECT "
        "postid"
        ", posts.filename AS image"
        ", owner"
        ", posts.created"
        ", users.filename AS owner_image"
        " FROM posts"
        " LEFT JOIN users"
        " ON owner = users.username"
        " WHERE posts.postid = '{}'".format(postid)
    ).fetchall()
    if len(post) == 0:
        return flask.redirect('/accounts/login/')  # post does not exist
    post = post[0]
    post["image"] = flask.url_for("download_file", filename=post["image"])
    post["owner_image"] = flask.url_for("download_file",
                                        filename=post["owner_image"])
    time = arrow.get(post["created"])
    post["created"] = time.humanize()

    # like info tracks:
    # -- number of likes
    # -- Boolean if logged in user likes post
    post["like_info"] = connection.execute(
        " SELECT"
        " SUM(CASE WHEN owner == '{}' THEN 1 ELSE 0 END) AS liked_by_logname"
        # track if logname likes post
        ", COUNT(*) AS like_count"
        " FROM likes"
        " WHERE"
        " postid = {}".format(user, post["postid"])
    ).fetchall()[0]

    # Faster to assign comments to posts through SQL calls than Python
    post["comments"] = connection.execute(
        "SELECT "
        "owner"
        ", commentid"
        ", postid"
        ", text"
        ", created"
        " FROM comments"
        " WHERE postid = {} ".format(post["postid"])
    ).fetchall()

    # Add database info to context
    context = {
        "logname": user,
        "post": post,
        "current_url": flask.request.path,
        "logged_in_user_page_url": '/users/{}'.format(user)
    }

    return flask.render_template("posts.html", **context)


@insta485.app.route('/posts/', methods=['POST'])
def edit_post():
    """Edit post by postid."""
    # Connect to database
    """ Requirement for All Pages """
    if "username" not in flask.session or not len(flask.session["username"]):
        return flask.redirect('/accounts/login/')
    user = flask.session["username"]
    if 'target' not in flask.request.args:
        target = '/users/{}/'.format(user)
    else:
        target = flask.request.args['target']

    # POST method: Create or delete a post

    operation = flask.request.form['operation']
    if operation == 'delete':
        postid = flask.request.form['postid']
        insta485.helpers.delete_post(user, postid)
    elif operation == 'create':
        # Unpack flask object
        fileobj = flask.request.files["file"]
        filename = fileobj.filename
        if len(filename) == 0:
            flask.abort(400)

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
        insta485.helpers.create_post(uuid_basename, user)
    return flask.redirect(target)


@insta485.app.route('/uploads/<path:filename>')
def download_file(filename):
    """Download file."""
    if "username" not in flask.session:
        flask.abort(403)
    elif not os.path.isfile(insta485.app.config['UPLOAD_FOLDER']/filename):
        flask.abort(404)
    return flask.send_from_directory(
        insta485.app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
