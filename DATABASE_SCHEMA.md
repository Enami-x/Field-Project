# AI Flashcard App: Database Schema (Supabase / PostgreSQL)

This document is the official "blueprint" for our Supabase database. All team members **must** use these exact table and column names to ensure our components work together.

**Data Model Philosophy (SQL):**
Our database is **relational**. This means we don't nest data. Instead, we use `Tables` and link them with `Foreign Keys`.

1.  **`profiles`**: Stores public user data. Links 1-to-1 with Supabase's built-in `auth.users` table.
2.  **`decks`**: Stores the *name* and *summary analytics* for a study deck.
3.  **`flashcards`**: A large table storing all *flashcards*. Each row is linked to a deck.
4.  **`quiz_questions`**: A large table storing all *quiz questions*. Each row is linked to a deck.
5.  **`quiz_attempts`**: A "log" table that stores the *history* of every quiz taken. This is our "Report Card."

---

## 1. Table: `auth.users` (Handled by Supabase)

This table is **automatically created and managed by Supabase Auth**. We don't touch it directly. When a user signs up, Supabase creates a row for them here.

* `id`: (Type: `uuid`) The user's unique ID. We will use this as a foreign key.
* `email`: (Type: `text`) The user's email.

---

## 2. Table: `profiles`

This table stores our app's public user data, like display names. It is linked 1-to-1 with the `auth.users` table.

**Created by:** **Member 2 (UX Lead)**, using a "trigger" or function that runs once, right after a new user signs up in `auth.users`.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `uuid` | **Primary Key**, **Foreign Key** `references auth.users(id)` | Must be the *exact same* `uuid` as the user in `auth.users`. |
| `email` | `text` | `unique` | A copy of the user's email, for convenience. |
| `display_name` | `text` | `nullable` | The user's name (can be added later via a "Profile" page). |
| `created_at` | `timestamp with time zone` | `default now()` | The date the user joined. |

---

## 3. Table: `decks`

This table stores the "header" information for a study deck and its summary analytics.

**Created by:** **Member 2 (UX Lead)**, after the AI functions (from Member 1) successfully return data.

**Read by:** **Member 3 (Analytics Lead)**, to populate the "Perfect/Practise More" dashboard.

**Updated by:** **Member 3 (Analytics Lead)**, who will update the `last_accuracy` column *every time* a quiz is completed.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` | **Primary Key** (`identity`) | An auto-incrementing unique ID for the deck. |
| **`user_id`** | `uuid` | **Foreign Key** `references profiles(id)` | **[CRITICAL]** Links this deck to its owner. |
| `name` | `text` | `not null` | The "Deck Name" the user entered (e.g., "PL/SQL Basics"). |
| `last_accuracy` | `integer` | `default 0` | The percentage score (0-100) of the *most recent* quiz attempt. |
| `source_text_length` | `integer` | | The length of the text used to generate this deck. |
| `created_at` | `timestamp with time zone` | `default now()` | The date the deck was created. |

---

## 4. Table: `flashcards`

This table stores every individual flashcard for every deck.

**Created by:** **Member 2 (UX Lead)**, who will "bulk insert" all the flashcards returned by the AI (from Member 1) after creating a new `deck`.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` | **Primary Key** (`identity`) | An auto-incrementing unique ID for the flashcard. |
| **`deck_id`** | `bigint` | **Foreign Key** `references decks(id) on delete cascade` | **[CRITICAL]** Links this card to its parent deck. |
| `question` | `text` | `not null` | The "front" of the flashcard. |
| `answer` | `text` | `not null` | The "back" of the flashcard. |

---

## 5. Table: `quiz_questions`

This table stores every individual quiz question for every deck.

**Created by:** **Member 2 (UX Lead)**, who will "bulk insert" all the quiz questions returned by the AI (from Member 1) after creating a new `deck`.

**Read by:** **Member 3 (Analytics Lead)**, to get the questions to run the quiz.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` | **Primary Key** (`identity`) | An auto-incrementing unique ID for the question. |
| **`deck_id`** | `bigint` | **Foreign Key** `references decks(id) on delete cascade` | **[CRITICAL]** Links this question to its parent deck. |
| `question` | `text` | `not null` | The text of the multiple-choice question. |
| `options` | `jsonb` | `not null` | The array of options, e.g., `["A", "B", "C", "D"]`. |
| `answer` | `text` | `not null` | The correct answer string from the `options` array. |

---

## 6. Table: `quiz_attempts`

This table is our "Report Card" log. Every single time a user completes a quiz, we **create one new row** in this table.

**Created by:** **Member 3 (Analytics Lead)**, every time a user submits a quiz.

**Read by:** **Member 3 (Analytics Lead)**, to build the "Report Card" history page for a specific deck.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` | **Primary Key** (`identity`) | An auto-incrementing unique ID for this attempt. |
| **`user_id`** | `uuid` | **Foreign Key** `references profiles(id) on delete cascade` | **[CRITICAL]** The `uid` of the user who took the quiz. |
| **`deck_id`** | `bigint` | **Foreign Key** `references decks(id) on delete cascade` | **[CRITICAL]** The ID of the deck this attempt belongs to. |
| `score` | `integer` | `not null` | The number of questions the user got right (e.g., `8`). |
| `total_questions` | `integer` | `not null` | The total number of questions in the quiz (e.g., `10`). |
| `accuracy` | `integer` | `not null` | The final percentage (e.g., `80`). |
| `answers_report` | `jsonb` | `nullable` | A JSON array storing the user's answers for review. `[{ "question": "...", "selectedAnswer": "...", "correctAnswer": "..." }]` |
| `created_at` | `timestamp with time zone` | `default now()` | **[CRITICAL]** The date/time the quiz was completed. |

---

## Summary of Relationships

* `profiles` (1) --- (Many) `decks` (A user can have many decks)
* `profiles` (1) --- (Many) `quiz_attempts` (A user can have many attempts)
* `decks` (1) --- (Many) `flashcards` (A deck has many flashcards)
* `decks` (1) --- (Many) `quiz_questions` (A deck has many quiz questions)
* `decks` (1) --- (Many) `quiz_attempts` (A deck can be attempted many times)
