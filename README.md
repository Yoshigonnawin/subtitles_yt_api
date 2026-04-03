# YouTube subtitles to plain text

Скрипт читает список YouTube-ссылок из `urls.txt`, вытаскивает готовые субтитры или авто-субтитры и сохраняет их как обычные `.txt` файлы в папку `output/`.

## Быстрый старт

```bash
uv sync
cp urls.example.txt urls.txt
uv run python main.py
```

Если нужен приоритет по языкам:

```bash
uv run python main.py --languages ru,en
```

Если хочешь в первую очередь брать авто-субтитры:

```bash
uv run python main.py --languages ru,en --prefer-auto
```

Если хочешь другой входной файл или папку результата:

```bash
uv run python main.py --input my_urls.txt --output-dir transcripts
```

## Что делать при HTTP 429

Если YouTube отвечает `Too Many Requests`, проблема обычно не в URL, а в антибот-лимите.

Сначала открой видео в браузере и обнови страницу, а затем попробуй один из вариантов:

```bash
uv run python main.py --cookies-from-browser firefox
```

или

```bash
uv run python main.py --cookies /path/to/cookies.txt
```

Если знаешь точный User-Agent браузера, можно передать и его:

```bash
uv run python main.py \
  --cookies-from-browser firefox \
  --user-agent "Mozilla/5.0 ..."
```

Дополнительно можно замедлить батч:

```bash
uv run python main.py --sleep-between-videos 5
```

## Формат входного файла

`urls.txt`:

```text
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
```

Пустые строки и строки, начинающиеся с `#`, игнорируются.

## Что получается на выходе

Для каждого ролика создается отдельный `.txt` файл:

```text
output/
  VIDEO_ID_Title.txt
```

Внутри файла есть:

- заголовок видео
- ссылка
- канал
- язык субтитров
- источник: обычные субтитры или авто-субтитры
- очищенный текст субтитров

## Ограничения

- Скрипт не делает транскрибацию аудио, он работает только с уже доступными субтитрами YouTube.
- Если у ролика нет ни обычных, ни авто-субтитров, файл создан не будет.
- `--cookies-from-browser` лучше всего работает, когда браузер доступен из той же среды, где запускается скрипт.
