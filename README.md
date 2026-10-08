# gha-demo-data

The data half of a GitHub Actions demo. Edit `data/coffee.csv`, and **Build data** does the rest:

1. `build`: `scripts/build_stats.py` turns the CSV into `dist/stats.json` and uploads it as the **stats-json** artifact.
2. `validate`: a fresh runner downloads the artifact and checks the totals add up.
3. `notify-site`: sends `repository_dispatch` (`data-updated`, with the run id) to **gha-demo-site**, which publishes the data to GitHub Pages.

If **Build data** fails on `main` in `build` or `validate`, **Claude fixes red builds** (`claude-fix.yml`) runs Claude Code through OpenRouter. It reads the failed log and opens a pull request with a fix. A person reviews and merges it.

Secrets:
- `CROSS_REPO_TOKEN`: a fine-grained PAT on both demo repos with Actions read, Contents read/write, and Pull requests read/write. It sends the dispatch, and the agent uses it to push its branch and open the PR.
- `OPENROUTER_API_KEY`: pays for the agent's model calls.

Optional variable: `OPENROUTER_MODEL` (default `anthropic/claude-sonnet-5.5`).

Live site: https://codebyjackson.github.io/gha-demo-site/

Run it locally:

```sh
python scripts/build_stats.py && python scripts/validate_stats.py dist/stats.json
```
