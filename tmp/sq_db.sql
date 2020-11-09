CREATE TABLE IF NOT EXISTS mainmenu (
id integer PRIMARY KEY AUTOINCREMENT,
title text NOT NULL,
url text NOT NULL
);

CREATE TABLE IF NOT EXISTS codes (
id integer PRIMARY KEY AUTOINCREMENT,
name text NOT NULL,
eng_name text NOT NULL,
nominal integer NOT NULL,
code text NOT NULL
);
DROP INDEX IF EXISTS idx_codes_code;
CREATE UNIQUE INDEX idx_codes_code ON codes (code);

CREATE TABLE IF NOT EXISTS rates (
id integer PRIMARY KEY AUTOINCREMENT,
currency_code text NOT NULL,
date_rate date NOT NULL,
exchange_rate float NOT NULL,
FOREIGN KEY(currency_code) REFERENCES codes(code),
UNIQUE(currency_code, date_rate)
);