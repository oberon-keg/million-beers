"""
Insta485 user (main) view.

URLs include:
/users
"""
import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/')
def show_user(user_url_slug):
    """Display /user route."""
    connection = insta485.model.get_db()

    if not flask.session.get('username'):
        return flask.redirect('/accounts/login')
    logname = flask.session["username"]

    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM users "
        "WHERE username = ?",
        (user_url_slug,)
    )
    does_exit = cur.fetchall()[0]["COUNT(*)"]
    print(does_exit)
    if does_exit == 0:
        flask.abort(404)

    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username1 = ? AND username2 = ?",
        (logname, user_url_slug)
    )
    is_following = cur.fetchall()

    cur = connection.execute(
        "SELECT filename, postid "
        "FROM posts "
        "WHERE owner = ?",
        (user_url_slug,)
    )
    posts = cur.fetchall()
    for post in posts:
        post["filename"] = \
            flask.url_for("download_file", filename=post["filename"])

    cur = connection.execute(
        "SELECT count(*)"
        "FROM following "
        "WHERE username1 = ?",
        (user_url_slug,)
    )

    num_following = cur.fetchall()[0]["count(*)"]

    cur = connection.execute(
        "SELECT count(*)"
        "FROM following "
        "WHERE username2 = ?",
        (user_url_slug,)
    )

    num_follower = cur.fetchall()[0]["count(*)"]

    cur = connection.execute(
        "SELECT fullname "
        "FROM users "
        "WHERE username = ?",
        (user_url_slug,)
    )

    fullname = cur.fetchall()[0]["fullname"]

    context = {
        "is_following": is_following[0]["COUNT(*)"],
        "logname": logname,
        "username": user_url_slug,
        "current_url": flask.request.path,
        "posts": posts,
        "num_posts": len(posts),
        "num_following": num_following,
        "num_follower": num_follower,
        "fullname": fullname
    }
    return flask.render_template("user.html", **context)


@insta485.app.route('/users/<user_url_slug>/followers/')
def show_followers(user_url_slug):
    """Display /user/slug/followers route."""
    connection = insta485.model.get_db()
    if not flask.session.get('username'):
        return flask.redirect('/accounts/login')
    logname = flask.session["username"]

    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM users "
        "WHERE username = ?",
        (user_url_slug,)
    )
    does_exit = cur.fetchall()[0]["COUNT(*)"]
    print(does_exit)
    if does_exit == 0:
        flask.abort(404)

    cur = connection.execute(
        "SELECT following.username1, users.filename "
        "FROM following "
        "LEFT JOIN users "
        "ON following.username1 = users.username "
        "WHERE following.username2 = ?",
        (user_url_slug, )
    )

    followers = cur.fetchall()

    cur = connection.execute(
        "SELECT following.username2 "
        "FROM following "
        "WHERE following.username1 = ?",
        (logname, )
    )

    compare = cur.fetchall()
    compare = [d['username2'] for d in compare]

    for follower in followers:
        follower["filename"] = \
            flask.url_for("download_file", filename=follower["filename"])
        follower["is_following"] = follower["username1"] in compare

    print(followers)

    context = {
        "logname": logname,
        "username": user_url_slug,
        "current_url": flask.request.path,
        "followers": followers
    }
    return flask.render_template("followers.html", **context)


@insta485.app.route('/users/<user_url_slug>/following/')
def show_following(user_url_slug):
    """Display /user/slug/followers route."""
    connection = insta485.model.get_db()
    if not flask.session.get('username'):
        return flask.redirect('/accounts/login')
    logname = flask.session["username"]

    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM users "
        "WHERE username = ?",
        (user_url_slug,)
    )
    does_exit = cur.fetchall()[0]["COUNT(*)"]
    print(does_exit)
    if does_exit == 0:
        flask.abort(404)

    cur = connection.execute(
        "SELECT following.username2, users.filename "
        "FROM following "
        "LEFT JOIN users "
        "ON following.username2 = users.username "
        "WHERE following.username1 = ?",
        (user_url_slug, )
    )

    followings = cur.fetchall()

    cur = connection.execute(
        "SELECT following.username2 "
        "FROM following "
        "WHERE following.username1 = ?",
        (logname, )
    )

    compare = cur.fetchall()
    compare = [d['username2'] for d in compare]

    for following in followings:
        following["filename"] = \
            flask.url_for("download_file", filename=following["filename"])
        following["is_following"] = following["username2"] in compare

    print(followings)

    context = {
        "logname": logname,
        "username": user_url_slug,
        "current_url": flask.request.path,
        "following": followings
    }
    return flask.render_template("following.html", **context)
