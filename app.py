from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime
from dotenv import load_dotenv
import paypalrestsdk

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')

# Database configuration for Vercel/Production
if os.environ.get('VERCEL'):
    # Use /tmp for SQLite on Vercel (read-only filesystem)
    # NOTE: Data will be wiped on every deployment. Use PostgreSQL for persistence.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/pubg_tournaments.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pubg_tournaments.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# PayPal Configuration
paypalrestsdk.configure({
    "mode": os.environ.get("PAYPAL_MODE", "sandbox"), # sandbox or live
    "client_id": os.environ.get("PAYPAL_CLIENT_ID", "YOUR_CLIENT_ID"),
    "client_secret": os.environ.get("PAYPAL_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
})

# Models
from models import User, Tournament, Registration, Payout, TournamentMatch, MatchResult, Donation, Sponsor
from pubg_api import PUBGAPI

pubg_api = PUBGAPI()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@app.route('/index')
def index():
    top_players = User.query.order_by(User.total_wins.desc()).limit(5).all()
    active_sponsors = Sponsor.query.all()
    return render_template('index.html', top_players=top_players, sponsors=active_sponsors)

@app.route('/tournament/<int:tournament_id>/donate', methods=['POST'])
def donate_to_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    amount = float(request.form.get('amount', 0))
    donor_name = request.form.get('donor_name', 'Anonymous')
    
    if amount > 0:
        donation = Donation(tournament_id=tournament.id, amount=amount, donor_name=donor_name)
        tournament.donation_total += amount
        db.session.add(donation)
        db.session.commit()
        flash(f"Thank you for your ${amount:.2f} donation!")
    return redirect(url_for('tournaments'))

@app.route('/tournament/<int:tournament_id>/earn-credit', methods=['POST'])
@login_required
def earn_sponsor_credit(tournament_id):
    # Simulated: User interacts with a sponsor (e.g., watches an ad)
    tournament = Tournament.query.get_or_404(tournament_id)
    credit_amount = 0.50 # Fixed credit per interaction
    tournament.sponsor_credit_total += credit_amount
    db.session.commit()
    flash(f"You earned ${credit_amount:.2f} in sponsor credit for this tournament prize pool!")
    return redirect(url_for('tournaments'))

@app.route('/tournament/<int:tournament_id>/sync-stats', methods=['POST'])
@login_required
def sync_tournament_stats(tournament_id):
    # This route would be used to fetch stats for a match in a tournament
    # In a real app, you might trigger this automatically or via webhook
    tournament = Tournament.query.get_or_404(tournament_id)
    match_id = request.form.get('match_id')
    
    if not match_id:
        flash("Match ID is required.")
        return redirect(url_for('tournaments'))

    match_data = pubg_api.get_match_details(tournament.platform, match_id)
    if not match_data:
        flash("Could not fetch match data from PUBG API.")
        return redirect(url_for('tournaments'))

    # Create match record
    new_match = TournamentMatch(tournament_id=tournament.id, match_id=match_id)
    db.session.add(new_match)
    
    # Process participants
    registrations = Registration.query.filter_by(tournament_id=tournament.id).all()
    for reg in registrations:
        user = User.query.get(reg.user_id)
        # Use xbox_gamertag or psn_id depending on platform
        gamertag = user.xbox_gamertag if tournament.platform.lower() == 'xbox' else user.psn_id
        
        if not gamertag:
            continue

        # Get player account ID (should ideally be stored in User model)
        player_data = pubg_api.get_player_stats(tournament.platform, gamertag)
        if player_data and 'data' in player_data:
            account_id = player_data['data'][0]['id']
            stats = pubg_api.extract_player_stats_from_match(match_data, account_id)
            
            if stats:
                result = MatchResult(
                    match=new_match,
                    user_id=user.id,
                    kills=stats['kills'],
                    placement=stats['placement'],
                    win=stats['win']
                )
                db.session.add(result)
                
                # Update user total stats
                user.total_kills += stats['kills']
                if stats['win']:
                    user.total_wins += 1
                    # Award prize for winning (Total Prize Pool = base + donations + sponsor credits)
                    user.balance += tournament.total_prize_pool 

    db.session.commit()
    flash("Stats synced and winners awarded!")
    return redirect(url_for('tournaments'))

@app.route('/tournaments')
def tournaments():
    all_tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
    return render_template('tournaments.html', tournaments=all_tournaments)

@app.route('/payout/<int:user_id>', methods=['POST'])
@login_required
def request_payout(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('index'))
    
    if user.balance <= 0:
        flash("Insufficient balance.")
        return redirect(url_for('index'))

    # Payout logic via PayPal
    payout = paypalrestsdk.Payout({
        "sender_batch_header": {
            "sender_batch_id": f"payout_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email_subject": "You have a tournament payout!"
        },
        "items": [
            {
                "recipient_type": "EMAIL",
                "amount": {
                    "value": f"{user.balance:.2f}",
                    "currency": "USD"
                },
                "receiver": user.paypal_email,
                "note": "Thank you for participating in PUBG Console Arena! Your payout includes donation funds and sponsor credits.",
                "sender_item_id": f"item_{user.id}"
            }
        ]
    })

    if payout.create():
        new_payout = Payout(user_id=user.id, amount=user.balance, status='completed')
        user.balance = 0
        db.session.add(new_payout)
        db.session.commit()
        flash("Payout successful! Check your PayPal account.")
    else:
        flash(f"Payout failed: {payout.error}")
        
    return redirect(url_for('index'))

# Mock Funding Source Logic
@app.route('/admin/add-tournament', methods=['GET', 'POST'])
def add_tournament():
    # In a real app, this would be restricted to admins
    if request.method == 'POST':
        title = request.form.get('title')
        prize = float(request.form.get('prize', 0))
        platform = request.form.get('platform')
        
        new_t = Tournament(
            title=title, 
            base_prize_pool=prize, 
            platform=platform,
            description="TPP Tournament",
            date=datetime.utcnow()
        )
        db.session.add(new_t)
        db.session.commit()
        flash("Tournament added successfully!")
        return redirect(url_for('tournaments'))
    
    return render_template('add_tournament.html')

@app.route('/admin/init-sponsors')
def init_sponsors():
    # Helper to add some placeholder sponsors
    if Sponsor.query.count() == 0:
        s1 = Sponsor(name="Razer", website_url="https://www.razer.com")
        s2 = Sponsor(name="Logitech G", website_url="https://www.logitechg.com")
        s3 = Sponsor(name="Red Bull", website_url="https://www.redbull.com")
        db.session.add_all([s1, s2, s3])
        db.session.commit()
        flash("Sponsors initialized!")
    return redirect(url_for('index'))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    current_user.xbox_gamertag = request.form.get('xbox_gamertag')
    current_user.psn_id = request.form.get('psn_id')
    current_user.paypal_email = request.form.get('paypal_email')
    db.session.commit()
    flash("Profile updated successfully!")
    return redirect(url_for('dashboard'))

@app.route('/login')
def login():
    flash("Login feature coming soon!")
    return redirect(url_for('index'))

@app.route('/register')
def register():
    flash("Registration feature coming soon!")
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Route to serve static docs locally for testing
@app.route('/static-preview/<path:filename>')
def static_preview(filename):
    from flask import send_from_directory
    return send_from_directory('docs', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
