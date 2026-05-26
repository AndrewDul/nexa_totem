# NeXa Learn Study Store

NeXa Learn is the local Study module for NeXa ToTem.

- SQLite database path: `var/data/study/nexa_study.db`.
- Tests can override the database with `NEXA_STUDY_DB_PATH`.
- The database and parent folder are created automatically.
- Schema version is `1` through SQLite `PRAGMA user_version`.
- `study_store.py` uses only Python standard library modules, including `sqlite3` and `difflib`.

The schema stores Pomodoro-compatible topics/sessions, Smart Study sessions, ordered Smart Study segments and notes, flashcard decks/cards/reviews, quiz sets/questions/attempts, language lists/words, generic notes, and study history events.

Duplicate and similar checks:
- Names are normalized by trimming, lowercasing, collapsing spaces, and removing obvious punctuation.
- Exact duplicates return `status: duplicate`.
- Similar names use `difflib.SequenceMatcher` and return `status: similar` at `0.82` similarity or higher.
- Similar warnings ask the user to refine the name instead of silently creating another item.

Features:
- Pomodoro-compatible storage remains for backend compatibility, but Smart Study is the user-facing session builder.
- Smart Study stores custom focus/break segments, validates minimum 5-minute focus and break parts, enforces alternating focus/break order, stores focus/session notes, and supports safe stop and finish actions.
- Flashcards persist decks, cards, typed review answers, checked/revealed-answer state, confidence, review statuses, and review counts.
- Flashcards support know, unsure, and don't-know outcomes, with repeat/unsure cards prioritized before known cards.
- Flashcards use a 50-correct threshold for mastered status.
- Quizzes persist quiz sets, questions, selected correct answer A/B/C/D, visible answer texts, answers, wrong/marked status, and attempts.
- Quiz and flashcard delete actions require confirmation and are intended to be reached after selecting one active item in the UI.
- Language Learning persists lists, words, pronunciation, meanings, selected-list detail, word deletion, correct/wrong review counts, weak/strong/mastered status, and mastered logic.
- Study History reads real saved events.
- Study Settings exposes database stats and delete actions.
- Delete-all requires a UI confirmation step and then `DELETE_STUDY_DATA`; deck, quiz, and language-list deletes require their specific confirmation strings.
- Study Stats returns totals and per-topic stats, including session count, total minutes, and last studied time.
