"""
Програма для проведення тенісного турніру в стилі ATP Finals
Кожен матч - один сет до 6 геймів з тайбрейком
"""
import random
from typing import List, Optional


class Player:
    """Клас для представлення гравця"""

    def __init__(self, name: str, seed: int = 0, level: Optional[float] = None):
        self.name = name
        self.seed = seed  # Посів гравця (1-8)
        self.level = level  # Рівень гри
        self.wins = 0
        self.losses = 0
        self.games_won = 0
        self.games_lost = 0

    def add_match_result(self, won: bool, games_won: int, games_lost: int):
        """Додає результат матчу до статистики гравця"""
        if won:
            self.wins += 1
        else:
            self.losses += 1
        self.games_won += games_won
        self.games_lost += games_lost

    def remove_match_result(self, won: bool, games_won: int, games_lost: int):
        """Видаляє результат матчу зі статистики гравця (для редагування)"""
        if won:
            self.wins -= 1
        else:
            self.losses -= 1
        self.games_won -= games_won
        self.games_lost -= games_lost

    def game_difference(self) -> int:
        """Повертає різницю геймів"""
        return self.games_won - self.games_lost

    def __str__(self):
        level_str = f", рівень {self.level}" if self.level else ""
        return f"{self.name} (#{self.seed}{level_str})"

    def __repr__(self):
        return self.__str__()


class Match:
    """Клас для представлення матчу (один сет)"""

    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.winner: Optional[Player] = None
        self.score: Optional[tuple[int, int]] = None

    def play(self, p1_games: int, p2_games: int):
        """Записує результат матчу"""
        # Якщо матч вже був зіграний, видаляємо стару статистику
        if self.score is not None and self.winner is not None:
            old_p1_games, old_p2_games = self.score
            if self.winner == self.player1:
                self.player1.remove_match_result(True, old_p1_games, old_p2_games)
                self.player2.remove_match_result(False, old_p2_games, old_p1_games)
            else:
                self.player2.remove_match_result(True, old_p2_games, old_p1_games)
                self.player1.remove_match_result(False, old_p1_games, old_p2_games)

        # Записуємо новий результат
        self.score = (p1_games, p2_games)
        if p1_games > p2_games:
            self.winner = self.player1
            self.player1.add_match_result(True, p1_games, p2_games)
            self.player2.add_match_result(False, p2_games, p1_games)
        else:
            self.winner = self.player2
            self.player2.add_match_result(True, p2_games, p1_games)
            self.player1.add_match_result(False, p1_games, p2_games)

    def __str__(self):
        if self.score:
            return f"{self.player1.name} {self.score[0]}-{self.score[1]} {self.player2.name}"
        return f"{self.player1.name} vs {self.player2.name}"


class ScheduledMatch(Match):
    """Клас для матчу з розкладом"""

    def __init__(self, player1: Player, player2: Player, time: str, court: int, round_num: int = 0, stage: str = "Group Stage"):
        super().__init__(player1, player2)
        self.time = time
        self.court = court
        self.round_num = round_num
        self.stage = stage

    def get_schedule_string(self) -> str:
        """Повертає рядок з інформацією про розклад"""
        status = ""
        if self.score:
            status = f" [{self.score[0]}-{self.score[1]}] ✅"
        return f"{self.time} | Корт {self.court} | {self.player1.name} vs {self.player2.name}{status}"


class Group:
    """Клас для групового етапу"""

    def __init__(self, name: str, players: List[Player]):
        self.name = name
        self.players = players
        self.matches: List[Match] = []
        self.scheduled_matches: List[ScheduledMatch] = []
        self._create_matches()

    def _create_matches(self):
        """Створює матчі раунд-робін (кожен з кожним) у правильному порядку для розкладу"""
        # Для групи з 4 гравцями [P0, P1, P2, P3] створюємо матчі так,
        # щоб у кожному раунді (по 2 матчі) всі гравці були різні:
        # Раунд 1: P0 vs P2, P1 vs P3
        # Раунд 2: P0 vs P3, P1 vs P2
        # Раунд 3: P0 vs P1, P2 vs P3

        if len(self.players) == 4:
            p0, p1, p2, p3 = self.players

            # Спеціальний порядок для групи з Vito
            player_names = [p.name for p in self.players]
            if "Vito" in player_names:
                # Порядок: ["Oleksandr", "Viktor", "Vito", "Yaroslav"]
                # p0 = Oleksandr, p1 = Viktor, p2 = Vito, p3 = Yaroslav
                # Раунд 1: Viktor vs Vito, Oleksandr vs Yaroslav
                self.matches.append(Match(p1, p2))
                self.matches.append(Match(p0, p3))
                # Раунд 2: Vito vs Yaroslav, Oleksandr vs Viktor
                self.matches.append(Match(p2, p3))
                self.matches.append(Match(p0, p1))
                # Раунд 3: Vito vs Oleksandr, Viktor vs Yaroslav
                self.matches.append(Match(p2, p0))
                self.matches.append(Match(p1, p3))
            else:
                # Стандартний порядок для групи B
                # Раунд 1
                self.matches.append(Match(p0, p2))
                self.matches.append(Match(p1, p3))
                # Раунд 2
                self.matches.append(Match(p0, p3))
                self.matches.append(Match(p1, p2))
                # Раунд 3
                self.matches.append(Match(p0, p1))
                self.matches.append(Match(p2, p3))
        else:
            # Якщо кількість гравців не 4, використовуємо стандартний метод
            for i in range(len(self.players)):
                for j in range(i + 1, len(self.players)):
                    self.matches.append(Match(self.players[i], self.players[j]))

    def get_standings(self) -> List[Player]:
        """Повертає таблицю гравців, відсортовану за результатами"""
        sorted_players = sorted(
            self.players,
            key=lambda p: (p.wins, p.game_difference(), p.games_won),
            reverse=True
        )
        return sorted_players

    def display_standings(self):
        """Виводить таблицю групи"""
        print(f"\n{'='*60}")
        print(f"Група {self.name}")
        print(f"{'='*60}")
        print(f"{'Гравець':<25} {'В':<5} {'П':<5} {'Геймі':<10} {'Різниця'}")
        print(f"{'-'*60}")

        for player in self.get_standings():
            games_str = f"{player.games_won}-{player.games_lost}"
            diff = f"+{player.game_difference()}" if player.game_difference() >= 0 else str(player.game_difference())
            print(f"{player.name:<25} {player.wins:<5} {player.losses:<5} {games_str:<10} {diff}")


class Tournament:
    """Головний клас турніру"""

    def __init__(self):
        self.players: List[Player] = []
        self.groups: List[Group] = []
        self.semifinals: List[Match] = []
        self.scheduled_semifinals: List[ScheduledMatch] = []
        self.third_place_match: Optional[Match] = None
        self.scheduled_third_place: Optional[ScheduledMatch] = None
        self.final: Optional[Match] = None
        self.scheduled_final: Optional[ScheduledMatch] = None

    def setup_players(self):
        """Встановлює учасників турніру"""
        print("\n🎾 Ласкаво просимо до ATP Finals Tournament Generator! 🎾\n")
        print("Учасники турніру (відсортовані за рівнем гри):\n")

        # Визначені учасники з рівнями гри
        participants = [
            ("Олександр", 4.0),
            ("Ігорь", 4.0),
            ("Марія", 4.0),
            ("Олексій", 3.75),
            ("Олег", 3.5),
            ("Віто", 3.5),
            ("Ярослав", 3.5),
            ("Віктор", 3.0),
        ]

        for i, (name, level) in enumerate(participants):
            player = Player(name, seed=i+1, level=level)
            self.players.append(player)
            level_display = f"рівень {level}" if level else "рівень невідомий"
            print(f"   #{i+1}. {name} ({level_display})")

    def create_schedule_for_groups(self):
        """Створює розклад матчів для групового етапу"""
        group_a = self.groups[0]
        group_b = self.groups[1]

        # Розклад: 3 раунди для кожної групи, по 2 матчі в раунді
        schedule = {
            "A": [
                ("8:00-9:00", [1, 2]),    # Раунд 1, група А
                ("10:00-11:00", [1, 2]),  # Раунд 2, група А
                ("12:00-13:00", [1, 2]),  # Раунд 3, група А
            ],
            "B": [
                ("9:00-10:00", [1, 2]),   # Раунд 1, група Б
                ("11:00-12:00", [1, 2]),  # Раунд 2, група Б
                ("13:00-14:00", [1, 2]),  # Раунд 3, група Б
            ]
        }

        # Для групи А
        for round_idx, (time_slot, courts) in enumerate(schedule["A"], 1):
            match_idx = (round_idx - 1) * 2
            for court_idx, court in enumerate(courts):
                if match_idx + court_idx < len(group_a.matches):
                    original_match = group_a.matches[match_idx + court_idx]
                    scheduled_match = ScheduledMatch(
                        original_match.player1,
                        original_match.player2,
                        time_slot,
                        court,
                        round_idx,
                        f"Group {group_a.name}"
                    )
                    group_a.scheduled_matches.append(scheduled_match)

        # Для групи Б
        for round_idx, (time_slot, courts) in enumerate(schedule["B"], 1):
            match_idx = (round_idx - 1) * 2
            for court_idx, court in enumerate(courts):
                if match_idx + court_idx < len(group_b.matches):
                    original_match = group_b.matches[match_idx + court_idx]
                    scheduled_match = ScheduledMatch(
                        original_match.player1,
                        original_match.player2,
                        time_slot,
                        court,
                        round_idx,
                        f"Group {group_b.name}"
                    )
                    group_b.scheduled_matches.append(scheduled_match)

    def display_full_schedule(self):
        """Відображає повний розклад турніру"""
        print("\n" + "="*70)
        print("📅 ПОВНИЙ РОЗКЛАД ТУРНІРУ 📅")
        print("="*70)

        # Груповий етап
        print("\n🎾 ГРУПОВИЙ ЕТАП")
        print("-"*70)

        all_scheduled_matches = []
        for group in self.groups:
            all_scheduled_matches.extend(group.scheduled_matches)

        # Сортуємо за часом
        time_slots = {}
        for match in all_scheduled_matches:
            if match.time not in time_slots:
                time_slots[match.time] = []
            time_slots[match.time].append(match)

        time_order = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00"]

        for time in time_order:
            if time in time_slots:
                matches = sorted(time_slots[time], key=lambda m: m.court)
                print(f"\n⏰ {time}")
                for match in matches:
                    print(f"   Корт {match.court} | {match.stage} | {match.player1.name} vs {match.player2.name}")

        # Плей-офф розклад (додамо потім)
        print("\n🏆 ПЛЕЙ-ОФФ")
        print("-"*70)
        print("\n⏰ 14:00-15:00")
        print("   Корт 1 | Півфінал 1 | Переможець групи A vs 2-е місце групи B")
        print("   Корт 2 | Півфінал 2 | Переможець групи B vs 2-е місце групи A")
        print("\n⏰ 15:00-16:00")
        print("   Корт 1 | Фінал | Переможці півфіналів")
        print("   Корт 2 | Матч за 3 місце | Переможені в півфіналах")
        print("="*70)

    def draw_groups(self):
        """Проводить жеребкування груп за рейтингом гри"""
        print("\n" + "="*60)
        print("ЖЕРЕБКУВАННЯ ГРУП")
        print("="*60)
        print("\nФіксований розподіл гравців по групах\n")

        # Фіксовані групи
        group_a_names = ["Oleksandr", "Viktor", "Vito", "Yaroslav"]
        group_b_names = ["Igor", "Oleksiy", "Oleg", "Prinston"]

        # Розподіляємо гравців по групах у заданому порядку
        group_a_players = []
        group_b_players = []

        # Додаємо гравців групи A в порядку group_a_names
        for name in group_a_names:
            for player in self.players:
                if player.name == name:
                    group_a_players.append(player)
                    break

        # Додаємо гравців групи B в порядку group_b_names
        for name in group_b_names:
            for player in self.players:
                if player.name == name:
                    group_b_players.append(player)
                    break

        self.groups = [
            Group("A", group_a_players),
            Group("B", group_b_players)
        ]

        print("📋 Група A:")
        for p in sorted(group_a_players, key=lambda x: -x.level):
            print(f"   • {p.name} (рівень {p.level})")

        print("\n📋 Група B:")
        for p in sorted(group_b_players, key=lambda x: -x.level):
            print(f"   • {p.name} (рівень {p.level})")

        # Показуємо баланс груп за рівнем
        avg_level_a = sum(p.level for p in group_a_players) / len(group_a_players)
        avg_level_b = sum(p.level for p in group_b_players) / len(group_b_players)
        print(f"\n💡 Середній рівень групи A: {avg_level_a:.2f}")
        print(f"💡 Середній рівень групи B: {avg_level_b:.2f}")
        print(f"💡 Різниця: {abs(avg_level_a - avg_level_b):.2f}")

    def play_group_stage(self):
        """Проводить груповий етап згідно з розкладом"""
        print("\n" + "="*70)
        print("ГРУПОВИЙ ЕТАП")
        print("="*70)
        print("(Кожен матч - один сет до 6 геймів з тайбрейком)")

        # Об'єднуємо всі матчі з обох груп і сортуємо за часом
        all_matches = []
        for group in self.groups:
            all_matches.extend(group.scheduled_matches)

        # Групуємо матчі за часовими слотами
        time_order = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00"]
        time_slots = {time: [] for time in time_order}

        for match in all_matches:
            if match.time in time_slots:
                time_slots[match.time].append(match)

        # Проходимо через кожен часовий слот
        for time_slot in time_order:
            matches_in_slot = sorted(time_slots[time_slot], key=lambda m: m.court)

            if not matches_in_slot:
                continue

            print("\n" + "="*70)
            print(f"⏰ {time_slot}")
            print("="*70)

            # Показуємо всі матчі в цьому слоті
            for match in matches_in_slot:
                print(f"Корт {match.court} | {match.stage} | {match.player1.name} vs {match.player2.name}")

            # Введення результатів для кожного матчу в слоті
            for match in matches_in_slot:
                print(f"\n🎾 Корт {match.court}: {match.player1.name} vs {match.player2.name}")

                while True:
                    try:
                        score = input(f"Введіть рахунок геймів (формат: X-Y, наприклад 6-4 або 7-6): ").strip()
                        p1_games, p2_games = map(int, score.split('-'))

                        if self._is_valid_tennis_score(p1_games, p2_games):
                            match.play(p1_games, p2_games)
                            print(f"✅ Результат: {match}")
                            break
                        else:
                            print("Некоректний теннісний рахунок!")
                            print("Валідні рахунки: 6-0, 6-1, 6-2, 6-3, 6-4, 7-5, 7-6 (і навпаки)")
                    except (ValueError, IndexError):
                        print("Неправильний формат! Використовуйте формат X-Y")

            # Після кожного часового слоту показуємо оновлені таблиці
            print("\n" + "📊 ПОТОЧНІ ТАБЛИЦІ ГРУП 📊")
            self.groups[0].display_standings()
            self.groups[1].display_standings()

        # Показуємо фінальні таблиці обох груп
        print("\n" + "="*70)
        print("🏁 ФІНАЛЬНІ ТАБЛИЦІ ГРУПОВОГО ЕТАПУ")
        print("="*70)
        self.groups[0].display_standings()
        self.groups[1].display_standings()

    def _is_valid_tennis_score(self, games1: int, games2: int) -> bool:
        """Перевіряє, чи є рахунок валідним теннісним рахунком для одного сету"""
        if games1 < 0 or games2 < 0:
            return False

        # Виграш 6-0, 6-1, 6-2, 6-3, 6-4
        if games1 == 6 and games2 <= 4:
            return True
        if games2 == 6 and games1 <= 4:
            return True

        # Виграш 7-5
        if (games1 == 7 and games2 == 5) or (games2 == 7 and games1 == 5):
            return True

        # Виграш 7-6 (тайбрейк)
        if (games1 == 7 and games2 == 6) or (games2 == 7 and games1 == 6):
            return True

        return False

    def setup_playoffs(self):
        """Налаштовує плей-офф раунди"""
        print("\n" + "="*70)
        print("ПЛЕЙ-ОФФ")
        print("="*70)

        # Беремо 2 найкращих з кожної групи
        group_a_standings = self.groups[0].get_standings()
        group_b_standings = self.groups[1].get_standings()

        a1, a2 = group_a_standings[0], group_a_standings[1]
        b1, b2 = group_b_standings[0], group_b_standings[1]

        print(f"\n🏆 Вихід з груп:")
        print(f"   Група A: {a1.name} (1-е місце), {a2.name} (2-е місце)")
        print(f"   Група B: {b1.name} (1-е місце), {b2.name} (2-е місце)")

        # Перехресні півфінали (переможець групи А грає з другим місцем групи Б і навпаки)
        sf1 = ScheduledMatch(a1, b2, "14:00-15:00", 1, 0, "Півфінал 1")
        sf2 = ScheduledMatch(b1, a2, "14:00-15:00", 2, 0, "Півфінал 2")

        self.scheduled_semifinals = [sf1, sf2]
        self.semifinals = [sf1, sf2]  # Зберігаємо для сумісності

        print(f"\n🎾 Півфінали (14:00-15:00):")
        print(f"   Корт 1 - Півфінал 1: {sf1.player1.name} vs {sf1.player2.name}")
        print(f"   Корт 2 - Півфінал 2: {sf2.player1.name} vs {sf2.player2.name}")

    def play_playoffs(self):
        """Проводить плей-офф матчі згідно з розкладом"""
        # ПІВФІНАЛИ
        print("\n" + "="*70)
        print("⏰ 14:00-15:00 - ПІВФІНАЛИ")
        print("="*70)

        winners = []
        losers = []

        # Показуємо обидва матчі
        for i, match in enumerate(self.scheduled_semifinals, 1):
            print(f"Корт {match.court} | {match.stage} | {match.player1.name} vs {match.player2.name}")

        # Грамо обидва півфінали
        for i, match in enumerate(self.scheduled_semifinals, 1):
            print(f"\n🎾 Корт {match.court} - Півфінал {i}: {match.player1.name} vs {match.player2.name}")

            while True:
                try:
                    score = input(f"Введіть рахунок (формат: X-Y): ").strip()
                    p1_games, p2_games = map(int, score.split('-'))

                    if self._is_valid_tennis_score(p1_games, p2_games):
                        match.play(p1_games, p2_games)
                        print(f"✅ Результат: {match}")
                        print(f"🏆 Переможець: {match.winner.name}")

                        winners.append(match.winner)
                        loser = match.player2 if match.winner == match.player1 else match.player1
                        losers.append(loser)
                        break
                    else:
                        print("Некоректний теннісний рахунок!")
                except (ValueError, IndexError):
                    print("Неправильний формат! Використовуйте формат X-Y")

        # ФІНАЛ та МАТЧ ЗА 3 МІСЦЕ
        print("\n" + "="*70)
        print("⏰ 15:00-16:00 - ФІНАЛ та МАТЧ ЗА 3 МІСЦЕ")
        print("="*70)

        # Створюємо scheduled матчі
        self.scheduled_final = ScheduledMatch(winners[0], winners[1], "15:00-16:00", 1, 0, "Фінал")
        self.scheduled_third_place = ScheduledMatch(losers[0], losers[1], "15:00-16:00", 2, 0, "Матч за 3 місце")

        self.final = self.scheduled_final
        self.third_place_match = self.scheduled_third_place

        # Показуємо обидва матчі
        print(f"Корт 1 | Фінал | {self.scheduled_final.player1.name} vs {self.scheduled_final.player2.name}")
        print(f"Корт 2 | Матч за 3 місце | {self.scheduled_third_place.player1.name} vs {self.scheduled_third_place.player2.name}")

        # Матч за 3 місце
        print(f"\n🥉 Корт 2 - Матч за 3 місце: {self.scheduled_third_place.player1.name} vs {self.scheduled_third_place.player2.name}")

        while True:
            try:
                score = input(f"Введіть рахунок (формат: X-Y): ").strip()
                p1_games, p2_games = map(int, score.split('-'))

                if self._is_valid_tennis_score(p1_games, p2_games):
                    self.scheduled_third_place.play(p1_games, p2_games)
                    print(f"✅ Результат: {self.scheduled_third_place}")
                    print(f"🥉 3 місце: {self.scheduled_third_place.winner.name}")
                    break
                else:
                    print("Некоректний теннісний рахунок!")
            except (ValueError, IndexError):
                print("Неправильний формат! Використовуйте формат X-Y")

        # Фінал
        print(f"\n🏆 Корт 1 - ФІНАЛ: {self.scheduled_final.player1.name} vs {self.scheduled_final.player2.name}")

        while True:
            try:
                score = input(f"Введіть рахунок (формат: X-Y): ").strip()
                p1_games, p2_games = map(int, score.split('-'))

                if self._is_valid_tennis_score(p1_games, p2_games):
                    self.scheduled_final.play(p1_games, p2_games)
                    print(f"✅ Результат: {self.scheduled_final}")
                    break
                else:
                    print("Некоректний теннісний рахунок!")
            except (ValueError, IndexError):
                print("Неправильний формат! Використовуйте формат X-Y")

    def display_final_results(self):
        """Виводить підсумкові результати турніру"""
        print("\n" + "="*60)
        print("🏆 ПІДСУМКИ ТУРНІРУ 🏆")
        print("="*60)

        fourth_place = self.third_place_match.player2 if self.third_place_match.winner == self.third_place_match.player1 else self.third_place_match.player1

        print(f"\n🥇 Чемпіон: {self.final.winner.name}")
        runner_up = self.final.player2 if self.final.winner == self.final.player1 else self.final.player1
        print(f"🥈 2 місце: {runner_up.name}")
        print(f"🥉 3 місце: {self.third_place_match.winner.name}")
        print(f"4️⃣  4 місце: {fourth_place.name}")

        print(f"\n🎉 Вітаємо переможця: {self.final.winner.name}! 🎉")

    def run(self):
        """Запускає весь турнір"""
        self.setup_players()
        self.draw_groups()
        self.create_schedule_for_groups()
        self.display_full_schedule()

        # Питаємо користувача чи готовий розпочати
        input("\nНатисніть Enter, щоб розпочати турнір...")

        self.play_group_stage()
        self.setup_playoffs()
        self.play_playoffs()
        self.display_final_results()


def main():
    """Головна функція програми"""
    tournament = Tournament()
    tournament.run()

    print("\n" + "="*60)
    print("Дякуємо за гру! До нових турнірів! 🎾")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
