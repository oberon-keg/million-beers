"""Reusable helpers to reduce code duplication."""

import os
import flask
import insta485


#  GETTERS


def get_comment_owner(commentid):
    """Return the owner of commentid."""
    connection = insta485.model.get_db()
    return connection.execute(
        'SELECT owner FROM comments WHERE commentid = ?', (commentid,)
    ).fetchall()[0]['owner']


def get_post_owner(postid):
    """Return the owner of postid."""
    connection = insta485.model.get_db()
    return connection.execute(
        'SELECT owner FROM posts '
        'WHERE postid = ?', (postid,)
    ).fetchall()[0]['owner']


def user_likes(logname, postid):
    """Return boolean indicating whether logname likes post."""
    connection = insta485.model.get_db()
    return connection.execute(
        'SELECT COUNT(*) > 0 AS user_likes_post'
        ' FROM likes WHERE owner = ? AND postid = ?', (logname, postid)
    ).fetchall()[0]['user_likes_post']


def user_follows(logname, userid):
    """Return boolean indicating whether logname follows userid."""
    connection = insta485.model.get_db()
    return connection.execute(
        'SELECT COUNT(*) > 0 AS logname_follows_user'
        ' FROM following WHERE username1 = ? \
            AND username2 = ? ', (logname, userid)
    ).fetchall()[0]['logname_follows_user']


def get_filename_from_postid(postid):
    """Return the filename of postid."""
    connection = insta485.model.get_db()
    return connection.execute(
        'SELECT filename FROM posts WHERE postid = ?',
        (postid,)
    ).fetchall()[0]['filename']

# SETTERS


def add_like(logname, postid):
    """Add 1 like to postid."""
    connection = insta485.model.get_db()
    user_likes_post = insta485.helpers.user_likes(logname, postid)

    # user already likes post
    if user_likes_post:
        flask.abort(409)

    connection.execute(
        'INSERT INTO likes '
        'VALUES(?, ?, ?, CURRENT_TIMESTAMP)',
        (None, logname, postid)
    )


def delete_like(logname, postid):
    """Delete 1 like from postid."""
    connection = insta485.model.get_db()
    user_likes_post = insta485.helpers.user_likes(logname, postid)

    # user already does not like post
    if not user_likes_post:
        flask.abort(409)

    connection.execute('DELETE FROM likes WHERE owner = ? \
        AND postid = ?', (logname, postid))


def add_comment(logname, postid, text):
    """Add a comment of 'str' to postid."""
    connection = insta485.model.get_db()
    connection.execute(
        'INSERT INTO comments '
        'VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)',
        (None, logname, postid, text)
    )


def delete_comment(logname, commentid):
    """Delete comment."""
    if logname != get_comment_owner(commentid):
        # unauthorized delete comment
        flask.abort(403)

    connection = insta485.model.get_db()
    connection.execute(
        'DELETE FROM comments '
        'WHERE commentid = ?',
        (commentid,)
    )


def add_follow(logname, user_to_follow):
    """Make logname follow user_to_follow."""
    # Check for user already following
    if user_follows(logname, user_to_follow):
        flask.abort(409)

    connection = insta485.model.get_db()
    connection.execute(
        'INSERT INTO following '
        'VALUES(?, ?, CURRENT_TIMESTAMP)',
        (logname, user_to_follow)
    )


def delete_post(logname, postid):
    """Delete a post given logname and postid."""
    if logname != get_post_owner(postid):
        # unauthorized delete post
        flask.abort(403)
    # get filename from postid
    filename = get_filename_from_postid(postid)
    # delete file
    os.remove(os.path.join(insta485.app.config['UPLOAD_FOLDER'], filename))
    connection = insta485.model.get_db()
    connection.execute(
        'DELETE FROM posts '
        'WHERE postid = ?',
        (postid,)
    )


def create_post(file, logname):
    """Create a new post."""
    if len(file) == 0:
        flask.abort(400)
    connection = insta485.model.get_db()
    connection.execute(
        'INSERT INTO posts '
        'VALUES(?, ?, ?, CURRENT_TIMESTAMP)',
        (None, file, logname)
    )


def create_user(username, fullname, email, filename, password):
    """Create a new user."""
    connection = insta485.model.get_db()
    connection.execute(
        'INSERT INTO users '
        'VALUES(?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
        (username, fullname, email, filename, password)
    )


def remove_follow(logname, user_to_unfollow):
    """Make logname unfollow user_to_unfollow."""
    # Check for user already unfollowed
    if not user_follows(logname, user_to_unfollow):
        flask.abort(409)

    connection = insta485.model.get_db()
    connection.execute(
        'DELETE FROM following '
        'WHERE username1 = ? AND username2 = ?',
        (logname, user_to_unfollow)
    )
