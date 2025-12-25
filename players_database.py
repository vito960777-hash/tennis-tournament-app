"""
Система зберігання та управління гравцями з рейтингом
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class PlayerDatabase:
    """Клас для управління базою даних гравців"""

    def __init__(self, db_file='players.json'):
        self.db_file = db_file
        self.players = self._load_players()

    def _load_players(self) -> Dict:
        """Завантажує гравців з файлу"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_players(self):
        """Зберігає гравців у файл"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.players, f, ensure_ascii=False, indent=2)

    def register_player(self, name: str, level: float = 1.0) -> Dict:
        """
        Реєструє нового гравця

        Args:
            name: Ім'я гравця
            level: Початковий рівень (1.0-10.0, NTRP система)

        Returns:
            Дані зареєстрованого гравця
        """
        if name in self.players:
            raise ValueError(f"Гравець {name} вже зареєстрований")

        player_data = {
            'name': name,
            'level': level,
            'rating': 1000,  # Початковий рейтинг
            'tournaments_played': 0,
            'total_wins': 0,
            'total_losses': 0,
            'registered_date': datetime.now().isoformat()
        }

        self.players[name] = player_data
        self._save_players()
        return player_data

    def get_player(self, name: str) -> Optional[Dict]:
        """Отримує дані гравця"""
        return self.players.get(name)

    def get_all_players(self) -> List[Dict]:
        """Отримує всіх гравців, відсортованих за рейтингом"""
        players_list = list(self.players.values())
        players_list.sort(key=lambda x: x['rating'], reverse=True)
        return players_list

    def update_rating(self, name: str, won: bool):
        """
        Оновлює рейтинг гравця після матчу

        Args:
            name: Ім'я гравця
            won: True якщо переміг, False якщо програв
        """
        if name not in self.players:
            return

        player = self.players[name]

        if won:
            player['rating'] += 100
            player['total_wins'] += 1
        else:
            player['rating'] -= 50
            player['total_losses'] += 1

        self._save_players()

    def revert_rating(self, name: str, won: bool):
        """
        Скасовує рейтинг гравця (для редагування результатів)

        Args:
            name: Ім'я гравця
            won: True якщо він виграв у попередньому результаті
        """
        if name not in self.players:
            return

        player = self.players[name]

        if won:
            player['rating'] -= 100
            player['total_wins'] -= 1
        else:
            player['rating'] += 50
            player['total_losses'] -= 1

        self._save_players()

    def update_tournament_stats(self, player_names: List[str]):
        """Оновлює статистику участі в турнірах"""
        for name in player_names:
            if name in self.players:
                self.players[name]['tournaments_played'] += 1
        self._save_players()

    def get_top_players(self, count: int = 8) -> List[str]:
        """
        Отримує топ-N гравців за рейтингом

        Args:
            count: Кількість гравців

        Returns:
            Список імен гравців
        """
        all_players = self.get_all_players()
        return [p['name'] for p in all_players[:count]]

    def player_exists(self, name: str) -> bool:
        """Перевіряє чи існує гравець"""
        return name in self.players

    def delete_player(self, name: str):
        """Видаляє гравця"""
        if name in self.players:
            del self.players[name]
            self._save_players()

    def update_player(self, name: str, level: Optional[float] = None, rating: Optional[int] = None):
        """
        Оновлює характеристики гравця

        Args:
            name: Ім'я гравця
            level: Новий рівень (1.0-10.0, NTRP система, підтримує 0.5 кроки)
            rating: Новий рейтинг
        """
        if name not in self.players:
            raise ValueError(f"Player {name} not found")

        player = self.players[name]

        if level is not None:
            if level < 1.0 or level > 10.0:
                raise ValueError("Level must be between 1.0 and 10.0")
            player['level'] = level

        if rating is not None:
            if rating < 0:
                raise ValueError("Rating cannot be negative")
            player['rating'] = rating

        self._save_players()

    def get_player_stats(self, name: str) -> Optional[Dict]:
        """Отримує статистику гравця"""
        if name not in self.players:
            return None

        player = self.players[name]
        total_matches = player['total_wins'] + player['total_losses']
        win_rate = (player['total_wins'] / total_matches * 100) if total_matches > 0 else 0

        return {
            'name': player['name'],
            'level': player['level'],
            'rating': player['rating'],
            'tournaments_played': player['tournaments_played'],
            'total_wins': player['total_wins'],
            'total_losses': player['total_losses'],
            'total_matches': total_matches,
            'win_rate': round(win_rate, 1)
        }
