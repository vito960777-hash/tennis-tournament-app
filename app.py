"""
Web interface for ATP Finals tennis tournament
Flask application for tournament management
"""
from flask import Flask, render_template, jsonify, request, session
from tennis_tournament import Player, Group, Tournament, ScheduledMatch
from players_database import PlayerDatabase
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Global tournament (shared by all users)
global_tournament = None

# Player database
player_db = PlayerDatabase()

# Admin password (change to your own!)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'tennis2024')


def get_tournament():
    """Gets the global tournament"""
    return global_tournament


def create_tournament():
    """Creates a new tournament"""
    global global_tournament

    # Check if there are enough players
    all_players = player_db.get_all_players()

    # If less than 10 players, create defaults
    if len(all_players) < 10:
        default_players = [
            # Group A
            ("Masha", 4),
            ("Oleksandr", 4),
            ("Yaroslav", 3.5),
            ("Vova", 3.5),
            ("Alex", 3.5),
            # Group B
            ("Igor", 4),
            ("Jonathan", 4),
            ("Oleg", 3.5),
            ("Vito", 3.5),
            ("Florian", 3.5),
        ]

        for name, level in default_players:
            if not player_db.player_exists(name):
                player_db.register_player(name, level)

        all_players = player_db.get_all_players()

    # Take top-10 players
    top_10 = all_players[:10]

    # Create tournament
    tournament = Tournament()
    tournament.players = []

    # Add players to tournament
    for i, player_data in enumerate(top_10):
        player = Player(
            name=player_data['name'],
            seed=i+1,
            level=player_data['level']
        )
        tournament.players.append(player)

    # Update tournament participation stats
    player_names = [p['name'] for p in top_10]
    player_db.update_tournament_stats(player_names)

    # Draw groups and create schedule
    tournament.draw_groups()
    tournament.create_schedule_for_groups()

    global_tournament = tournament
    return tournament


def is_admin():
    """Checks if the user is an admin"""
    return session.get('is_admin', False)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/auth/login', methods=['POST'])
def admin_login():
    """Admin login"""
    data = request.json
    password = data.get('password')

    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid password'}), 401


@app.route('/api/auth/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session['is_admin'] = False
    return jsonify({'success': True, 'message': 'Logout successful'})


@app.route('/api/auth/status')
def auth_status():
    """Checks authorization status"""
    return jsonify({'is_admin': is_admin()})


@app.route('/api/tournament/new', methods=['POST'])
def new_tournament():
    """Creates a new tournament (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can create tournament'}), 403

    tournament = create_tournament()

    return jsonify({
        'success': True,
        'message': 'Tournament created successfully'
    })


@app.route('/api/tournament/info')
def tournament_info():
    """Returns tournament information"""
    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Tournament not found'}), 404

    # Format group data
    groups_data = []
    for group in tournament.groups:
        players_data = []
        for player in group.get_standings():
            players_data.append({
                'name': player.name,
                'seed': player.seed,
                'level': player.level,
                'wins': player.wins,
                'losses': player.losses,
                'games_won': player.games_won,
                'games_lost': player.games_lost,
                'game_difference': player.game_difference()
            })

        groups_data.append({
            'name': group.name,
            'players': players_data
        })

    # Format group stage match data
    group_matches = []
    for group in tournament.groups:
        for match in group.scheduled_matches:
            group_matches.append({
                'time': match.time,
                'court': match.court,
                'stage': match.stage,
                'player1': match.player1.name,
                'player2': match.player2.name,
                'score': match.score,
                'played': match.score is not None
            })

    return jsonify({
        'groups': groups_data,
        'group_matches': group_matches,
        'is_admin': is_admin()
    })


@app.route('/api/tournament/schedule')
def tournament_schedule():
    """Returns tournament schedule"""
    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Tournament not found'}), 404

    schedule = []

    # Group stage
    for group in tournament.groups:
        for match in group.scheduled_matches:
            schedule.append({
                'time': match.time,
                'court': match.court,
                'stage': match.stage,
                'player1': match.player1.name,
                'player2': match.player2.name,
                'score': match.score,
                'played': match.score is not None,
                'type': 'group'
            })

    # Playoffs (if exists)
    if tournament.scheduled_semifinals:
        for i, match in enumerate(tournament.scheduled_semifinals, 1):
            schedule.append({
                'time': match.time,
                'court': match.court,
                'stage': match.stage,
                'player1': match.player1.name,
                'player2': match.player2.name,
                'score': match.score,
                'played': match.score is not None,
                'type': 'playoff',
                'playoff_type': 'semifinal'
            })

    if tournament.scheduled_final:
        schedule.append({
            'time': tournament.scheduled_final.time,
            'court': tournament.scheduled_final.court,
            'stage': tournament.scheduled_final.stage,
            'player1': tournament.scheduled_final.player1.name,
            'player2': tournament.scheduled_final.player2.name,
            'score': tournament.scheduled_final.score,
            'played': tournament.scheduled_final.score is not None,
            'type': 'playoff',
            'playoff_type': 'final'
        })

    if tournament.scheduled_third_place:
        schedule.append({
            'time': tournament.scheduled_third_place.time,
            'court': tournament.scheduled_third_place.court,
            'stage': tournament.scheduled_third_place.stage,
            'player1': tournament.scheduled_third_place.player1.name,
            'player2': tournament.scheduled_third_place.player2.name,
            'score': tournament.scheduled_third_place.score,
            'played': tournament.scheduled_third_place.score is not None,
            'type': 'playoff',
            'playoff_type': 'third_place'
        })

    return jsonify({'schedule': schedule})


@app.route('/api/match/submit', methods=['POST'])
def submit_match():
    """Submits match result (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can submit results'}), 403

    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Tournament not found'}), 404

    data = request.json
    player1_name = data.get('player1')
    player2_name = data.get('player2')
    score = data.get('score')  # Format: "2-0" or "2-1" (sets)
    match_type = data.get('type', 'group')

    try:
        p1_sets, p2_sets = map(int, score.split('-'))

        # Validate score (Next Gen format: 2-0, 2-1, 0-2, 1-2)
        if not tournament._is_valid_tennis_score(p1_sets, p2_sets):
            return jsonify({'error': 'Invalid score. Valid: 2-0, 2-1, 0-2, 1-2'}), 400

        # Find match
        match_found = False

        if match_type == 'group':
            for group in tournament.groups:
                for match in group.scheduled_matches:
                    if (match.player1.name == player1_name and
                        match.player2.name == player2_name):

                        # Save new result
                        match.play(p1_sets, p2_sets)
                        match_found = True
                        break
                if match_found:
                    break

        if not match_found:
            return jsonify({'error': 'Match not found'}), 404

        return jsonify({'success': True, 'message': 'Result saved'})

    except ValueError:
        return jsonify({'error': 'Invalid score format'}), 400


@app.route('/api/playoffs/setup', methods=['POST'])
def setup_playoffs():
    """Sets up playoffs (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can setup playoffs'}), 403

    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Tournament not found'}), 404

    # Check if all group matches are played
    all_played = True
    for group in tournament.groups:
        for match in group.scheduled_matches:
            if match.score is None:
                all_played = False
                break

    if not all_played:
        return jsonify({'error': 'Not all group matches are played'}), 400

    tournament.setup_playoffs()

    return jsonify({'success': True, 'message': 'Playoffs setup complete'})


@app.route('/api/playoffs/match', methods=['POST'])
def submit_playoff_match():
    """Submits playoff match result (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can submit results'}), 403

    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Tournament not found'}), 404

    data = request.json
    player1_name = data.get('player1')
    player2_name = data.get('player2')
    score = data.get('score')  # Format: "2-0" or "2-1" (sets)
    playoff_type = data.get('playoff_type')  # 'semifinal', 'final', 'third_place'

    try:
        p1_sets, p2_sets = map(int, score.split('-'))

        if not tournament._is_valid_tennis_score(p1_sets, p2_sets):
            return jsonify({'error': 'Invalid score. Valid: 2-0, 2-1, 0-2, 1-2'}), 400

        # Find corresponding match
        if playoff_type == 'semifinal':
            for match in tournament.scheduled_semifinals:
                if (match.player1.name == player1_name and
                    match.player2.name == player2_name):

                    match.play(p1_sets, p2_sets)

                    # If both semifinals are played, create/update final
                    if all(m.score is not None for m in tournament.scheduled_semifinals):
                        winners = [m.winner for m in tournament.scheduled_semifinals]
                        losers = []
                        for m in tournament.scheduled_semifinals:
                            loser = m.player2 if m.winner == m.player1 else m.player1
                            losers.append(loser)

                        # Check if final already exists
                        if tournament.scheduled_final:
                            # Reset old final stats if it was played
                            if tournament.scheduled_final.score is not None:
                                tournament.scheduled_final.score = None
                                tournament.scheduled_final.winner = None

                        if tournament.scheduled_third_place:
                            # Reset 3rd place match stats if it was played
                            if tournament.scheduled_third_place.score is not None:
                                tournament.scheduled_third_place.score = None
                                tournament.scheduled_third_place.winner = None

                        tournament.scheduled_final = ScheduledMatch(
                            winners[0], winners[1], "20:00", 1, 0, "Final"
                        )
                        tournament.scheduled_third_place = ScheduledMatch(
                            losers[0], losers[1], "19:00", 1, 0, "3rd Place Match"
                        )
                        tournament.final = tournament.scheduled_final
                        tournament.third_place_match = tournament.scheduled_third_place

                    return jsonify({'success': True, 'message': 'Result saved'})

        elif playoff_type == 'final' and tournament.scheduled_final:
            if (tournament.scheduled_final.player1.name == player1_name and
                tournament.scheduled_final.player2.name == player2_name):

                tournament.scheduled_final.play(p1_sets, p2_sets)

                return jsonify({'success': True, 'message': 'Final completed!'})

        elif playoff_type == 'third_place' and tournament.scheduled_third_place:
            if (tournament.scheduled_third_place.player1.name == player1_name and
                tournament.scheduled_third_place.player2.name == player2_name):

                tournament.scheduled_third_place.play(p1_sets, p2_sets)
                return jsonify({'success': True, 'message': 'Third place match completed!'})

        return jsonify({'error': 'Match not found'}), 404

    except ValueError:
        return jsonify({'error': 'Invalid score format'}), 400


@app.route('/api/results')
def final_results():
    """Returns final tournament results"""
    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Tournament not found'}), 404

    if not tournament.final or not tournament.final.winner:
        return jsonify({'error': 'Tournament not yet completed'}), 400

    runner_up = (tournament.final.player2 if tournament.final.winner == tournament.final.player1
                 else tournament.final.player1)

    fourth_place = None
    if tournament.third_place_match and tournament.third_place_match.winner:
        fourth_place = (tournament.third_place_match.player2
                       if tournament.third_place_match.winner == tournament.third_place_match.player1
                       else tournament.third_place_match.player1)

    return jsonify({
        'champion': tournament.final.winner.name,
        'runner_up': runner_up.name,
        'third_place': tournament.third_place_match.winner.name if tournament.third_place_match else None,
        'fourth_place': fourth_place.name if fourth_place else None
    })


# ===== API for player management =====

@app.route('/api/players')
def get_players():
    """Returns list of all players"""
    players = player_db.get_all_players()
    return jsonify({'players': players})


@app.route('/api/players/<name>')
def get_player_stats(name):
    """Returns detailed player statistics"""
    stats = player_db.get_player_stats(name)

    if not stats:
        return jsonify({'error': 'Player not found'}), 404

    return jsonify(stats)


@app.route('/api/players', methods=['POST'])
def register_player():
    """Registers a new player (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can register players'}), 403

    data = request.json
    name = data.get('name')
    level = data.get('level', 1)

    if not name:
        return jsonify({'error': 'Player name is required'}), 400

    if not (1 <= level <= 10):
        return jsonify({'error': 'Level must be between 1 and 10'}), 400

    try:
        player = player_db.register_player(name, level)
        return jsonify({
            'success': True,
            'message': f'Player {name} successfully registered',
            'player': player
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/players/<name>', methods=['PUT'])
def update_player(name):
    """Updates player data (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can update players'}), 403

    if not player_db.player_exists(name):
        return jsonify({'error': 'Player not found'}), 404

    data = request.json
    level = data.get('level')

    try:
        player_db.update_player(name, level=level)
        return jsonify({
            'success': True,
            'message': f'Player {name} updated',
            'player': player_db.get_player(name)
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/players/<name>', methods=['DELETE'])
def delete_player(name):
    """Deletes a player (admin only)"""
    if not is_admin():
        return jsonify({'error': 'Only administrator can delete players'}), 403

    if not player_db.player_exists(name):
        return jsonify({'error': 'Player not found'}), 404

    player_db.delete_player(name)
    return jsonify({
        'success': True,
        'message': f'Player {name} deleted'
    })


if __name__ == '__main__':
    # Debug mode for local development only
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')
