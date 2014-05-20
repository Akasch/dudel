from dudel import app, db, login_manager, gravatar
from flask import abort
import scrypt
import random

def update_user_data(username, data):
    user = User.query.filter_by(username=username).first()
    if not user:
        # create the user
        user = User()
        user.username = username
        db.session.add(user)

    if "givenName" in data:
        user.firstname = data["givenName"]
    if "displayName" in data:
        user._displayname = data["displayName"]
    else:
        user._displayname = None
    user.lastname = data["sn"]
    user.email = data["mail"]
    db.session.commit()

# password stuff (scrypt yay)

def randstr(length):
    return ''.join(chr(random.randint(0,255)) for i in range(length))

def hash_password(password, maxtime=0.5, datalength=256):
    salt = randstr(datalength)
    hashed_password = scrypt.encrypt(salt, password.encode('utf-8'), maxtime=maxtime)
    return bytearray(hashed_password)

def verify_password(hashed_password, guessed_password, maxtime=300):
    try:
        scrypt.decrypt(hashed_password, guessed_password.encode('utf-8'), maxtime)
        return True
    except scrypt.error as e:
        print "scrypt error: %s" % e    # Not fatal but a necessary measure if server is under heavy load
        return False


@login_manager.user_loader
def get_user(username):
    return User.query.filter_by(username=username).first()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80))
    lastname = db.Column(db.String(80))
    username = db.Column(db.String(80))
    password = db.Column(db.LargeBinary)
    _displayname = db.Column(db.String(80))
    email = db.Column(db.String(80))
    preferred_language = db.Column(db.String(80))

    # relationships
    polls = db.relationship("Poll", backref="author", lazy="dynamic")
    watches = db.relationship("PollWatch", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    comments = db.relationship("Comment", backref="user", lazy="dynamic")
    votes = db.relationship("Vote", backref="user", lazy="dynamic")

    @property
    def displayname(self):
        return self._displayname or ((app.config["NAME_FORMAT"] if "NAME_FORMAT" in app.config else "%(firstname)s (%(username)s)") % {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "username": self.username,
            "email": self.email
            })
    # login stuff
    def get_id(self):
        return self.username

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        return "ADMINS" in app.config and self.username in app.config["ADMINS"]

    def require_admin(self):
        if not self.is_authenticated() or not self.is_admin:
            abort(403)

    def set_password(self, password):
        self.password = hash_password(password.encode("ascii"))

    def get_avatar(self, size):
        return gravatar(self.email, size)

    @property
    def poll_list(self):
        # TODO: try to do it in SQL
        watched = [watch.poll for watch in self.watches if not watch.poll.deleted]
        owned = self.polls.filter_by(deleted=False).all()
        voted = [vote.poll for vote in self.votes if not vote.poll.deleted]
        all = watched + owned + voted
        all = list(set(all))
        all.sort(key=lambda x: x.created, reverse=True)
        return all
