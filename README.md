# SOTheme

Dark and light Islands UI themes with syntax color schemes for PHP, Blade, HTML, CSS, JavaScript, and the block terminal in JetBrains IDEs (2026.2+).

## Themes

- **SOTheme Dark**: deep navy workspace (`#0F1320`) with violet accents (`#8B5CF6`) and balanced syntax contrast.
- **SOTheme Light**: warm cream workspace (`#FAF6EE`) with high-contrast dark text (`#0D0F12`) and readable ANSI terminal colors.

## Build & Verify

```bash
python3 olustur.py
python3 -m unittest discover -s . -p "test_*.py" -v
```

Output is generated under `dist/SOTheme-<version>.jar` along with standalone `.icls` color schemes.

## License

[MIT](LICENSE)
