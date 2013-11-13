from dudel import app, db
from flask import url_for, session
from datetime import datetime

def get_user(username):
    return User.query.filter_by(username=username).first() or AnonymousUser(username)

class AnonymousUser(object):
    def __init__(self, username):
        self.anonymous = True
        self.username = username

    def get_id(self):
        return self.username

    def is_active(self):
        return not self.anonymous

    def is_anonymous(self):
        return self.anonymous

    def is_authenticated(self):
        return not self.anonymous

class User(db.Model, AnonymousUser):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    token = db.Column(db.String(64))

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    slug = db.Column(db.String(80))
    type = db.Column(db.Enum("date", "normal"), default="normal")
    created = db.Column(db.DateTime)
    author = db.relationship("User", backref="polls")
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # extra settings
    due_date = db.Column(db.DateTime)
    password = db.Column(db.String)
    password_mode = db.Column(db.Enum("show", "vote"))
    anonymous_allowed = db.Column(db.Boolean, default=True)
    require_login = db.Column(db.Boolean, default=False)
    show_results = db.Column(db.Enum("summary", "complete", "never", "summary_after_vote", "complete_after_vote"))

    def __init__(self):
        self.created = datetime.utcnow()

    def get_url(self):
        return url_for("poll", slug=self.slug)

    def get_vote_choice(self, vote, choice):
        return VoteChoice.query.filter_by(vote=vote, choice=choice).first()

    def get_choices(self):
        return Choice.query.filter_by(poll_id=self.id, deleted=False).all()

    def get_choice_dates(self):
        return list(set([choice.date.date() for choice in self.get_choices()]))

    def get_choice_times(self):
        return list(set([choice.date.time() for choice in self.get_choices()]))

    def has_choice_date_time(self, date, time):
        dt = datetime.combine(date, time)
        return [choice for choice in self.get_choices() if choice.date == dt and not choice.deleted]

    # def get_vote(self, user):
    #     return Vote.query.filter_by(self.)

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    poll = db.relationship("Poll", backref="choices")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    deleted = db.Column(db.Boolean, default=False)

    def __cmp__(self,other):
        return cmp(self.date, other.date) or cmp(self.deleted, other.deleted) or cmp(self.text, other.text)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    poll = db.relationship("Poll", backref="votes")
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    user = db.relationship("User", backref="votes")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notice = db.Column(db.String(64))
    value = db.Column(db.Enum("yes", "no", "maybe"), default="no")
    vote = db.relationship("Vote", backref="vote_choices")
    vote_id = db.Column(db.Integer, db.ForeignKey("vote.id"))
    choice = db.relationship("Choice", backref="vote_choices")
    choide_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
