# Google News CLI

A simple and elegant command-line application written in Node.js to fetch and display the latest news from Google News RSS feeds.

## Features

- **Latest Headlines:** Default action retrieves current top stories.
- **Search Query:** Search news for specific topics or keywords.
- **Limit Results:** Custom limit on the number of articles displayed.
- **Country & Language Selection:** Fetch news targeted to specific countries and languages (e.g. Hindi in India, French in France, etc.).
- **Clickable Links:** Clean, colorized terminal output with direct article links.

## Prerequisites

- [Node.js](https://nodejs.org/) (version 18 or higher recommended)

## Installation

1. Navigate to the project directory:
   ```bash
   cd my-first-project
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Usage

Run the script using Node:

```bash
node index.js [options]
```

### Options

| Flag | Alias | Description | Default |
| :--- | :--- | :--- | :--- |
| `--search <query>` | `-s` | Search for specific topics or keywords | N/A (Top Headlines) |
| `--limit <number>` | `-l` | Limit the number of headlines displayed | `10` |
| `--country <code>` | `-c` | Set country/region code (ISO 3166-1 alpha-2) | `US` |
| `--lang <code>`    | N/A  | Set language code (ISO 639-1) | `en` |
| `--help`           | `-h` | Display this help menu | N/A |

### Examples

- **Get the top 10 news headlines in the US (Default):**
  ```bash
  node index.js
  ```

- **Get top 5 headlines about space travel:**
  ```bash
  node index.js --search "space exploration" --limit 5
  ```

- **Get top headlines in the UK:**
  ```bash
  node index.js --country GB
  ```

- **Get French news from France:**
  ```bash
  node index.js --country FR --lang fr
  ```
