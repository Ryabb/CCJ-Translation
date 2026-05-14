#!/usr/bin/env python3
"""
recolor_titles.py — Proportional multi-color tag applicator for titles.txt

For entries where the Japanese KEY has multiple <color=...>char</color> segments
(e.g. each character is a different colour), the English VALUE is rewritten so
those same colours are distributed proportionally across the English characters.

Single-color and uncolored entries are left untouched.

Usage:
    py recolor_titles.py
    py recolor_titles.py path/to/titles.txt
    py recolor_titles.py path/to/titles.txt --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DEFAULT_TITLES = (
    Path(__file__).parent.parent.parent
    / "BepInEx" / "Translation" / "en" / "Text" / "titles.txt"
)


def unescape(s: str) -> str:
    return s.replace(r'\=', '=').replace(r'\\', '\\')


def escape(s: str) -> str:
    return s.replace('=', r'\=')


def strip_tags(s: str) -> str:
    return re.sub(r'<[^>]+>', '', s)


def _char_split(segments, en, prefix):
    """Proportional character-level split — used when there are no spaces."""
    total_jp = sum(len(t) for _, t in segments) or 1
    parts = [prefix]
    pos = 0
    for i, (color, jp_text) in enumerate(segments):
        if i == len(segments) - 1:
            chunk = en[pos:]
        else:
            n = max(1, round(len(jp_text) / total_jp * len(en)))
            n = min(n, len(en) - pos - (len(segments) - 1 - i))
            chunk = en[pos:pos + n]
            pos += n
        parts.append(f'<color={color}>{chunk}</color>')
    return escape(''.join(parts))


def _word_split(segments, words, prefix):
    """
    Assign each word to the proportionally matching colour segment,
    then group consecutive words with the same colour together.
    Spaces are preserved as trailing whitespace inside each colour tag.
    """
    total_jp = sum(len(t) for _, t in segments) or 1
    n_segs   = len(segments)

    # Determine which segment each word belongs to based on its centre position
    seg_for_word = []
    for w_i in range(len(words)):
        centre     = (w_i + 0.5) / len(words)
        cumulative = 0
        assigned   = n_segs - 1
        for s_i, (color, jp_text) in enumerate(segments):
            cumulative += len(jp_text) / total_jp
            if centre <= cumulative:
                assigned = s_i
                break
        seg_for_word.append(assigned)

    # Group consecutive words that share the same colour segment
    groups: list[tuple[int, list[str]]] = []
    for word, seg in zip(words, seg_for_word):
        if groups and groups[-1][0] == seg:
            groups[-1][1].append(word)
        else:
            groups.append((seg, [word]))

    parts = [prefix]
    for g_i, (seg_idx, grp_words) in enumerate(groups):
        color = segments[seg_idx][0]
        text  = ' '.join(grp_words)
        if g_i < len(groups) - 1:
            text += ' '   # keep the space that was between this group and the next
        parts.append(f'<color={color}>{text}</color>')

    return escape(''.join(parts))


def proportional_recolor(key_unescaped: str, en_text: str) -> str | None:
    """
    Parse multi-color segments from the Japanese key and distribute
    the English text proportionally across those colours.

    - Multiple words → word-based split (no word is cut mid-character).
    - Single word    → character-based split (existing behaviour).

    Returns the new escaped English value, or None if not applicable.
    """
    sprite_match = re.match(r'^(<sprite[^>]+>)', key_unescaped)
    prefix = sprite_match.group(1) if sprite_match else ''

    segments = re.findall(r'<color=([^>]+)>(.*?)</color>',
                          key_unescaped, re.DOTALL)

    if len(segments) <= 1:
        return None

    en = strip_tags(unescape(en_text))

    if len(en) < len(segments):
        return None

    words = en.split(' ')

    # Use word-based split only when there are enough words to give every
    # colour segment at least one word. Otherwise fall back to character split
    # so all colours are actually used (e.g. "Big Spender" with 5 colours).
    if len(words) >= len(segments):
        return _word_split(segments, words, prefix)
    else:
        return _char_split(segments, en, prefix)


def process(titles_path: Path, dry_run: bool) -> None:
    content = titles_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)

    new_lines = []
    changed = 0

    for line in lines:
        m = re.search(r'(?<!\\)=', line)
        if not m:
            new_lines.append(line)
            continue

        jp_key_escaped = line[:m.start()]
        en_value = line[m.end():]
        newline_suffix = ''
        if en_value.endswith('\n'):
            newline_suffix = '\n'
            en_value = en_value[:-1]

        jp_unescaped = unescape(jp_key_escaped)
        new_en = proportional_recolor(jp_unescaped, en_value)

        if new_en is not None and new_en != en_value:
            changed += 1
            if dry_run:
                print(f"WOULD CHANGE:")
                print(f"  KEY: {jp_key_escaped}")
                print(f"  OLD: {en_value}")
                print(f"  NEW: {new_en}")
            new_lines.append(f'{jp_key_escaped}={new_en}{newline_suffix}')
        else:
            new_lines.append(line)

    if not dry_run:
        titles_path.write_text(''.join(new_lines), encoding='utf-8')

    action = "Would change" if dry_run else "Changed"
    print(f"{action} {changed} entries in {titles_path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('titles', nargs='?', type=Path, default=DEFAULT_TITLES,
                        help=f'Path to titles.txt (default: {DEFAULT_TITLES})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would change without writing')
    args = parser.parse_args()

    if not args.titles.exists():
        print(f"ERROR: file not found: {args.titles}", file=sys.stderr)
        sys.exit(1)

    process(args.titles, args.dry_run)


if __name__ == '__main__':
    main()
