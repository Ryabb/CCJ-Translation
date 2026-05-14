# Scripts

Helper scripts for the CCJ-Translation project. All scripts load `DEEPL_API_KEY` and `ANTHROPIC_API_KEY` from a `.env` file in the project root if present.

---

## deepl_verify.py

Verifies existing English translations against DeepL and lets you review and apply better ones.

**What it does:**
1. Reads translation `.txt` files and sends each Japanese key to DeepL.
2. Compares DeepL's result against the current English value using word-overlap similarity.
3. Entries below the similarity threshold are flagged.
4. Entries whose DeepL translation contains a word from `AUTO_ACCEPT_KEYWORDS` are applied automatically.
5. Remaining flagged entries open in a review UI — two buttons let you keep the existing translation or replace it with DeepL's. Tags (color, sprite) are preserved automatically.

**Requirements:** `pip install requests`

**Usage:**
```
py deepl_verify.py
py deepl_verify.py --files gameplay.txt missions.txt
py deepl_verify.py --files gameplay.txt --limit 50
py deepl_verify.py --threshold 0.3
py deepl_verify.py --refresh-glossary
py deepl_verify.py --no-ui
```

**Key options:**

| Flag | Description |
|------|-------------|
| `--files` | Which `.txt` files to verify (default: all) |
| `--limit N` | Only check the first N entries per file |
| `--threshold` | Similarity cutoff (0–1, default 0.4). Lower = flag more |
| `--input-dir` | Directory containing the translation files |
| `--glossary` | Path to glossary TSV (default: `deepl_glossary.tsv` next to this script) |
| `--refresh-glossary` | Force re-upload of the glossary to DeepL |
| `--no-ui` | Skip the review UI, just write the TSV report |

**Generated files** (all gitignored, written to the working directory):
- `deepl_cache.txt` — cached JP→EN translations to avoid re-charging API quota
- `deepl_glossary_id.txt` — cached DeepL glossary ID and content hash
- `deepl_verification_report.tsv` — full comparison report

---

## deepl_glossary.tsv

Term glossary used by `deepl_verify.py` to ensure consistent translation of game-specific terms (character names, mechanics, etc.). Tab-separated `Japanese→English`. Lines starting with `#` are comments.

The glossary is uploaded to DeepL on first use and automatically re-uploaded when the file changes.

---

## generate_filehash_name.py

Renames texture files to the `name [NAMEHASH-DATAHASH].ext` format expected by XUnity.AutoTranslator (`TextureHashGenerationStrategy=FromImageName`).

**What it does:**
- Computes two SHA1-based hashes per file: one from the filename, one from the file contents.
- Renames the file in-place, stripping any existing hash suffix first.

**Requirements:** standard library only

**Note:** due to XUnity hash nature the second hash part is not accurate to the hash generated from dumped textures. This script should be used mainly on assets extracted from the game. 

**Usage:**
```
py generate_filehash_name.py <folder>
py generate_filehash_name.py <folder> --recursive
py generate_filehash_name.py <folder> --dry-run
py generate_filehash_name.py <folder> --extensions .png .jpg
```

---

## translate_card.py

Batch translates card/item-obtain textures using Claude Vision.

**What it does:**
- Reads every PNG/JPG in the input folder.
- Overlays a template image, sends it to Claude to extract and translate the Japanese title.
- Redraws the card with the English text and saves to the output folder.

**Requirements:** `pip install pillow anthropic`

**Environment variables:**
- `ANTHROPIC_API_KEY` — required
- `TEMPLATE_PATH` — path to the overlay template PNG (default: `item_obtain_template.png`)
- `FONT_PATH` — path to `TCG2SAB.ttf` (default: `TCG2SAB.ttf`)

**Usage:**
```
py translate_card.py <input_folder> <output_folder>
```

---

## translate_sprite.py

Batch translates in-game sprite textures that contain Japanese text using Claude Vision.

**What it does:**
- Detects Japanese text in the lower region of each PNG/JPG.
- Sends the image to Claude to get the English translation.
- Erases the original Japanese text and redraws with the English translation.
- Verifies placement accuracy using IoU (intersection over union).

**Requirements:** `pip install pillow anthropic numpy`

**Environment variables:**
- `ANTHROPIC_API_KEY` — required
- `FONT_PATH` — path to `TCG2SAB.ttf` (default: `TCG2SAB.ttf`)

**Usage:**
```
py translate_sprite.py <input_folder> <output_folder>
```
