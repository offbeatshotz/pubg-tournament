from extensions import db
from flask_login import UserMixin
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    paypal_email = db.Column(db.String(120), nullable=True)
    platform = db.Column(db.String(20), nullable=False) # PS5 or Xbox Series
    xbox_gamertag = db.Column(db.String(80), nullable=True)
    psn_id = db.Column(db.String(80), nullable=True)
    xbox_oauth_id = db.Column(db.String(100), nullable=True, unique=True)
    psn_oauth_id = db.Column(db.String(100), nullable=True, unique=True)
    balance = db.Column(db.Float, default=0.0)
    total_kills = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    base_prize_pool = db.Column(db.Float, default=0.0)
    donation_total = db.Column(db.Float, default=0.0)
    sponsor_credit_total = db.Column(db.Float, default=0.0)
    platform = db.Column(db.String(20), nullable=False) # PS5, Xbox Series, or Crossplay
    status = db.Column(db.String(20), default='upcoming') # upcoming, ongoing, completed
    max_players = db.Column(db.Integer, default=100)
    matches = db.relationship('TournamentMatch', backref='tournament', lazy=True)

    @property
    def total_prize_pool(self):
        return self.base_prize_pool + self.donation_total + self.sponsor_credit_total

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    donor_name = db.Column(db.String(80), default='Anonymous')
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    contribution_type = db.Column(db.String(50)) # e.g., 'Per View', 'Direct Credit'

class TournamentMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    match_id = db.Column(db.String(100), nullable=True) # PUBG API Match ID
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('MatchResult', backref='match', lazy=True)

class MatchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('tournament_match.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kills = db.Column(db.Integer, default=0)
    placement = db.Column(db.Integer, default=0)
    win = db.Column(db.Boolean, default=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Payout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, completed, failed
    paypal_transaction_id = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
