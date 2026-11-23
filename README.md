# news-image-20261122-v7

One image summing up the world news of **Sunday 22 November 2026**.

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

[![rank](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v7/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard)
[![reward](https://make.fun/badge/news-image-20261122/Misaka450/news-image-20261122-v7/reward.svg)](https://make.fun/bounty/news-image-20261122)

20 stories across seven regions, every one dated and every one illustrated. Three hero
cards open the page, twelve more follow, and five close it; a four-cell ledger of the
day's hard numbers, a UTC timeline, a pinned world map, and a date-check strip that
names what was left out and why.

## Run

```bash
python3 build.py     # writes entry.png and preview-300.png (1024x1024, <=1 MiB)
python3 main.py      # copies entry.png to $MAKEFUN_OUTPUT_DIR/entry.png
```

No network, no image models: everything is drawn with Pillow.

## License

MIT
