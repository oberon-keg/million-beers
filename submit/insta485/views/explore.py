"""
Insta485 index (main) view.

URLs include:
/
"""

import flask
import insta485


@insta485.app.route('/explore/')
def show_explore():
    """Display /explore route."""
    connection = insta485.model.get_db()
    logname = flask.session["username"]

    cur = connection.execute(
        "SELECT following.username2 "
        "FROM following "
        "WHERE username1 = ?",
        (logname, )
    )

    compare = cur.fetchall()
    compare = [d['username2'] for d in compare]
    compare.append(logname)
    print(compare)
    temp = cur = connection.execute(
        "SELECT following.username2, following.username1 "
        "FROM following "
    ).fetchall()
    print(temp)

    cur = connection.execute(
        "SELECT DISTINCT username, fullname, filename "
        "FROM users "
    )

    not_following = cur.fetchall()
    not_following = (
        [user for user in not_following if user["username"] not in compare])
    for user in not_following:
        user["filename"] = \
            flask.url_for("download_file", filename=user["filename"])
    print(not_following)
    context = {
        "current_url": flask.request.path,
        "not_following": not_following,
        "username": logname
    }
    return flask.render_template("explore.html", **context)
