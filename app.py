"""
Веб-інтерфейс для тенісного турніру ATP Finals
Flask додаток для управління турніром
"""
from flask import Flask, render_template, jsonify, request, session
from tennis_tournament import Player, Group, Tournament, ScheduledMatch
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Глобальний турнір (один для всіх користувачів)
global_tournament = None

# Адмін пароль (змініть на свій!)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'tennis2024')


def get_tournament():
    """Отримує глобальний турнір"""
    return global_tournament


def create_tournament():
    """Створює новий турнір"""
    global global_tournament

    tournament = Tournament()
    tournament.setup_players()
    tournament.draw_groups()
    tournament.create_schedule_for_groups()

    global_tournament = tournament
    return tournament


def is_admin():
    """Перевіряє чи користувач - адмін"""
    return session.get('is_admin', False)


@app.route('/')
def index():
    """Головна сторінка"""
    return render_template('index.html')


@app.route('/api/auth/login', methods=['POST'])
def admin_login():
    """Адмін логін"""
    data = request.json
    password = data.get('password')

    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Вхід виконано'})
    else:
        return jsonify({'success': False, 'message': 'Невірний пароль'}), 401


@app.route('/api/auth/logout', methods=['POST'])
def admin_logout():
    """Адмін вихід"""
    session['is_admin'] = False
    return jsonify({'success': True, 'message': 'Вихід виконано'})


@app.route('/api/auth/status')
def auth_status():
    """Перевіряє статус авторизації"""
    return jsonify({'is_admin': is_admin()})


@app.route('/api/tournament/new', methods=['POST'])
def new_tournament():
    """Створює новий турнір (тільки адмін)"""
    if not is_admin():
        return jsonify({'error': 'Тільки адміністратор може створити турнір'}), 403

    tournament = create_tournament()

    return jsonify({
        'success': True,
        'message': 'Турнір створено успішно'
    })


@app.route('/api/tournament/info')
def tournament_info():
    """Повертає інформацію про турнір"""
    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Турнір не знайдено'}), 404

    # Формуємо дані про групи
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

    # Формуємо дані про матчі групового етапу
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
    """Повертає розклад турніру"""
    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Турнір не знайдено'}), 404

    schedule = []

    # Груповий етап
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

    # Плей-офф (якщо є)
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
    """Приймає результат матчу (тільки адмін)"""
    if not is_admin():
        return jsonify({'error': 'Тільки адміністратор може вносити результати'}), 403

    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Турнір не знайдено'}), 404

    data = request.json
    player1_name = data.get('player1')
    player2_name = data.get('player2')
    score = data.get('score')  # Формат: "6-4"
    match_type = data.get('type', 'group')

    try:
        p1_games, p2_games = map(int, score.split('-'))

        # Валідація рахунку
        if not tournament._is_valid_tennis_score(p1_games, p2_games):
            return jsonify({'error': 'Некоректний теннісний рахунок'}), 400

        # Знаходимо матч
        match_found = False

        if match_type == 'group':
            for group in tournament.groups:
                for match in group.scheduled_matches:
                    if (match.player1.name == player1_name and
                        match.player2.name == player2_name):
                        match.play(p1_games, p2_games)
                        match_found = True
                        break
                if match_found:
                    break

        if not match_found:
            return jsonify({'error': 'Матч не знайдено'}), 404

        return jsonify({'success': True, 'message': 'Результат збережено'})

    except ValueError:
        return jsonify({'error': 'Неправильний формат рахунку'}), 400


@app.route('/api/playoffs/setup', methods=['POST'])
def setup_playoffs():
    """Налаштовує плей-офф (тільки адмін)"""
    if not is_admin():
        return jsonify({'error': 'Тільки адміністратор може налаштувати плей-офф'}), 403

    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Турнір не знайдено'}), 404

    # Перевіряємо, чи всі групові матчі зіграні
    all_played = True
    for group in tournament.groups:
        for match in group.scheduled_matches:
            if match.score is None:
                all_played = False
                break

    if not all_played:
        return jsonify({'error': 'Не всі групові матчі зіграні'}), 400

    tournament.setup_playoffs()

    return jsonify({'success': True, 'message': 'Плей-офф налаштовано'})


@app.route('/api/playoffs/match', methods=['POST'])
def submit_playoff_match():
    """Приймає результат плей-офф матчу (тільки адмін)"""
    if not is_admin():
        return jsonify({'error': 'Тільки адміністратор може вносити результати'}), 403

    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Турнір не знайдено'}), 404

    data = request.json
    player1_name = data.get('player1')
    player2_name = data.get('player2')
    score = data.get('score')
    playoff_type = data.get('playoff_type')  # 'semifinal', 'final', 'third_place'

    try:
        p1_games, p2_games = map(int, score.split('-'))

        if not tournament._is_valid_tennis_score(p1_games, p2_games):
            return jsonify({'error': 'Некоректний теннісний рахунок'}), 400

        # Знаходимо відповідний матч
        if playoff_type == 'semifinal':
            for match in tournament.scheduled_semifinals:
                if (match.player1.name == player1_name and
                    match.player2.name == player2_name):
                    match.play(p1_games, p2_games)

                    # Якщо обидва півфінали зіграні, створюємо/оновлюємо фінал
                    if all(m.score is not None for m in tournament.scheduled_semifinals):
                        winners = [m.winner for m in tournament.scheduled_semifinals]
                        losers = []
                        for m in tournament.scheduled_semifinals:
                            loser = m.player2 if m.winner == m.player1 else m.player1
                            losers.append(loser)

                        # Перевіряємо чи фінал вже існує
                        if tournament.scheduled_final:
                            # Скидаємо статистику старого фіналу якщо він був зіграний
                            if tournament.scheduled_final.score is not None:
                                tournament.scheduled_final.score = None
                                tournament.scheduled_final.winner = None

                        if tournament.scheduled_third_place:
                            # Скидаємо статистику матчу за 3 місце якщо він був зіграний
                            if tournament.scheduled_third_place.score is not None:
                                tournament.scheduled_third_place.score = None
                                tournament.scheduled_third_place.winner = None

                        tournament.scheduled_final = ScheduledMatch(
                            winners[0], winners[1], "15:00-16:00", 1, 0, "Фінал"
                        )
                        tournament.scheduled_third_place = ScheduledMatch(
                            losers[0], losers[1], "15:00-16:00", 2, 0, "Матч за 3 місце"
                        )
                        tournament.final = tournament.scheduled_final
                        tournament.third_place_match = tournament.scheduled_third_place

                    return jsonify({'success': True, 'message': 'Результат збережено'})

        elif playoff_type == 'final' and tournament.scheduled_final:
            if (tournament.scheduled_final.player1.name == player1_name and
                tournament.scheduled_final.player2.name == player2_name):
                tournament.scheduled_final.play(p1_games, p2_games)
                return jsonify({'success': True, 'message': 'Фінал завершено!'})

        elif playoff_type == 'third_place' and tournament.scheduled_third_place:
            if (tournament.scheduled_third_place.player1.name == player1_name and
                tournament.scheduled_third_place.player2.name == player2_name):
                tournament.scheduled_third_place.play(p1_games, p2_games)
                return jsonify({'success': True, 'message': 'Матч за 3 місце завершено!'})

        return jsonify({'error': 'Матч не знайдено'}), 404

    except ValueError:
        return jsonify({'error': 'Неправильний формат рахунку'}), 400


@app.route('/api/results')
def final_results():
    """Повертає фінальні результати турніру"""
    tournament = get_tournament()

    if not tournament:
        return jsonify({'error': 'Турнір не знайдено'}), 404

    if not tournament.final or not tournament.final.winner:
        return jsonify({'error': 'Турнір ще не завершений'}), 400

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


if __name__ == '__main__':
    # Debug режим тільки для локальної розробки
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')
