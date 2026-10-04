"""Contrat du moteur : un adaptateur Ollama pourra remplacer LocalBrain."""
from typing import Protocol, Sequence, Mapping


class Brain(Protocol):
    def reply(self, text: str, history: Sequence[Mapping[str, str]]) -> str:
        ...


class LocalBrain:
    def reply(self, text: str, history: Sequence[Mapping[str, str]]) -> str:
        normalized = text.casefold().strip()
        if normalized in ("bonjour", "salut", "hello", "bonsoir"):
            return "Bonjour ! Je suis IA-LEX. Utilise /help pour découvrir mes commandes."
        if "souviens" in normalized or "dernier message" in normalized:
            previous = next((item["content"] for item in reversed(history) if item["role"] == "user"), None)
            return f"Ton dernier message enregistré : {previous}" if previous else "Je n’ai pas encore de souvenir."
        if "qui es" in normalized:
            return "Je suis IA-LEX Personal V1, ton assistant local Python. Mon moteur V1 utilise des règles simples."
        return "Message reçu. Je le conserve dans ta mémoire locale. Mon moteur V1 est simple ; un moteur Ollama pourra être ajouté ensuite."
