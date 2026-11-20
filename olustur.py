#!/usr/bin/env python3
"""SOTheme üreteci.

JetBrains'in yerleşik "Islands Dark" ve "Islands Light" arayüz temalarından
kalıtım alarak SOTheme renk paletlerini uygular, PHP/Blade ağırlıklı editör
şemalarını üretir ve PhpStorm / JetBrains Marketplace uyumlu eklenti jar'ını
paketler.

Kullanım:  python3 olustur.py
Çıktı:     src/  (eklenti kaynakları)   dist/ (SOTheme-<sürüm>.jar ve .icls dosyaları)
"""

import json
import shutil
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

SURUM = "1.2.0"
KOK = Path(__file__).resolve().parent
SRC = KOK / "src"
DIST = KOK / "dist"

# ---------------------------------------------------------------------------
# Arayüz paletleri (Islands Dark / Islands Light named color değerlerini ezer)
# ---------------------------------------------------------------------------

KOYU_RAMPA = {
    "gray": ["#0F1320", "#141927", "#1A2030", "#222939", "#2B3345", "#384154", "#4A5367", "#5E677C",
             "#757E93", "#8C95AA", "#A3ABBE", "#B8BFD0", "#CBD1DF", "#DBE0EA", "#E8ECF3", "#F5F7FA"],
    "blue": ["#101A33", "#13203F", "#17274C", "#1C2F5C", "#223A70", "#2A4789", "#3457A8", "#3F68C9",
             "#5680E6", "#6E97F5", "#8EAFFA", "#AAC3FC", "#C4D5FE", "#D8E3FF", "#E8EFFF", "#F5F8FF"],
}

ACIK_RAMPA = {
    "gray": ["#0D0F12", "#15181E", "#1D212A", "#262B35", "#303642", "#3A414E", "#3F4654", "#4E5666",
             "#666E7D", "#858B96", "#A8A396", "#C2BDB0", "#D5CFC1", "#E3DDD0", "#EDE7DA", "#F5F0E4"],
    "blue": ["#0E1833", "#132045", "#172856", "#1C3170", "#1E3A8A", "#1E43A8", "#1D4FD0", "#2563EB",
             "#4B7FF1", "#6B97F7", "#8BB0FA", "#A9C5FC", "#C7D9FE", "#DBE7FE", "#EAF1FF", "#F5F8FF"],
}

KOYU_SEMANTIK = {
    "transparent": "#0F132000",
    "editor-text": "#D6DCEB",
    "main-window-bg": "#0A0D16",
    "accent-brand-bg": "#8B5CF6",
    "accent-brand-border": "#8B5CF6",
    "accent-brand-bg-secondary": "#2A2152",
    "accent-brand-border-secondary": "#4C3A91",
    "selection-bg-active": "#1E2C52",
    "selection-bg-active-muted": "#18223F",
    "toolbar-selected-bg": "#3B2D78",
    "toolbar-selected-bg-hovered": "#47378F",
    "tab-selected-bg-active": "#1A2238",
    "tab-selected-border-active": "#8B5CF6",
    "tab-file-color-mask-bg": "#0F132080",
    "got-it-bg": "#3B2D78",
    "got-it-border": "#3B2D78",
    "presentation-assistant-bg": "#3B2D78",
    "popup-completion-match-text": "#A78BFA",
    "search-match-bg": "#B08A3E",
    "icon-default-stroke": "#B8BFD0",
}

ACIK_SEMANTIK = {
    "white": "#FCF9F2",
    "transparent": "#FAF6EE00",
    "editor-text": "#0D0F12",
    "editor-bg": "#FAF6EE",
    "editor-border-alt": "#E2DCCE",
    "tool-window-bg": "#FAF6EE",
    "tool-window-bg-alt": "#F4EFE4",
    "main-window-bg-alt": "#EAE4D7",
    "tab-selected-bg-active": "#E4EDFE",
    "tab-selected-border-active": "#2563EB",
    "tab-file-color-mask-bg": "#FAF6EE80",
    "popup-completion-match-text": "#1D4ED8",
    "search-match-bg": "#FDE7A6",
}

# Ebeveyn Islands temalarında named color yerine sabit hex kullanan birkaç alan
KOYU_UI_EK = {
    "LineProfiler": {
        "Line": {"foreground": "gray-100"},
        "IgnoredLine": {"foreground": "gray-80"},
    },
    "NuGet": {
        "section": {"background": "gray-20"},
    },
    "Recap": {
        "cardBackground": "gray-20",
        "chroniclesBackground": "gray-30",
        "chroniclesBorderColor": "gray-30",
        "chroniclesBackgroundHovered": "gray-40",
    },
}

ACIK_UI_EK = {
    "NuGet": {
        "section": {"background": "gray-160"},
    },
}

# ---------------------------------------------------------------------------
# Editör paletleri
# ---------------------------------------------------------------------------

NORMAL, KALIN, ITALIK = 0, 1, 2
ALT_CIZGI, DALGA, USTU_CIZILI = 1, 2, 3

KOYU = {
    "ad": "SOTheme Dark", "ebeveyn": "Darcula",
    # sözdizimi
    # Midnight Pro: lacivert zemin, lavanta keyword, turkuaz sınıf, açık mavi fonksiyon,
    # sarı değişken, lime string, kırmızı <?php, pembe HTML/Blade, mor tip/arayüz
    "bg": "0F1320", "fg": "D6DCEB", "keyword": "C4B5FD", "class": "5EEAD4", "type": "A78BFA",
    "function": "7DB4FF", "variable": "E8DC7A", "field": "D6DCEB", "string": "B9E57A",
    "number": "F5A97F", "comment": "667089", "php_tag": "F87171", "html_tag": "F9A8D4",
    "attr": "E8DC7A", "operator": "A9B3CC", "punct": "A9B3CC", "named_arg": "93C5FD",
    "escape": "5EEAD4", "doc_tag": "C4B5FD", "metadata": "F9A8D4",
    # editör yüzeyi
    "caret": "A78BFA", "caret_row": "151B2B", "selection": "25365E", "line_nr": "414A60",
    "line_nr_caret": "C3CADB", "indent": "1C2233", "indent_sel": "3A4360", "whitespace": "2C3348",
    "popup": "151A29", "fold_bg": "1F2740", "fold_fg": "8C95AA", "search": "4A4020",
    "search_stripe": "C9A24A", "text_search": "173F4A", "under_caret": "1F2A48",
    "under_caret_write": "3A2440", "brace": "2C3656", "inlay_fg": "8088A0", "inlay_bg": "1C2236",
    "template_bg": "131929", "added": "4ADE80", "modified": "6E97F5", "deleted": "64708A",
    "error": "F87171", "warning": "FBBF24", "weak_warning": "8A7A4A", "typo": "86EFAC",
    "link": "8EAFFA", "todo": "5EEAD4", "unused": "586079", "hint_bg": "1A2136",
    "diff_ins": "15332A", "diff_mod": "1A2A4F", "diff_del": "35222E", "diff_conf": "3A3120",
    "breakpoint": "3A1E28", "exec": "1F3460",
    "console_sys": "8C95AA",
    "term_block_start": "141927", "term_sel_bg": "1E2C52",
    "term_hover_start": "FFFFFF0A", "term_hover_end": "FFFFFF03",
    "ansi": ["2B3345", "F87171", "B9E57A", "E8DC7A", "7DB4FF", "C4B5FD", "5EEAD4", "A9B3CC",
             "8C95AA", "FCA5A5", "D0F2A0", "F3EAA0", "A5CBFF", "DDD3FE", "99F6E4", "F1F4FA"],
    "ansi_bg": ["1A2030", "4A1D24", "1B3B2B", "4A3B18", "1C315E", "33245C", "163E42", "2B3345",
                "384154", "63232C", "244F38", "614D1C", "25427D", "45307A", "1D5359", "CBD1DF"],
}

ACIK = {
    "ad": "SOTheme Light", "ebeveyn": "Default",
    # Soft krem zemin, tam koyu siyah ana metin, koyu antrasit griler ve yüksek kontrastlı terminal
    "bg": "FAF6EE", "fg": "0D0F12", "keyword": "6D28D9", "class": "1D4ED8", "type": "1E3A8A",
    "function": "0E7490", "variable": "B91C1C", "field": "92400E", "string": "15803D",
    "number": "B45309", "comment": "434A57", "php_tag": "BE185D", "html_tag": "C2410C",
    "attr": "92400E", "operator": "262C36", "punct": "1E232B", "named_arg": "4338CA",
    "escape": "0E7490", "doc_tag": "6D28D9", "metadata": "92400E",
    # PHP kodu ve anahtar kelimeleri "Light with Light Header" teki gibi kalın
    "php_keyword_font": KALIN, "php_scripting_font": KALIN,
    "caret": "6D28D9", "caret_row": "F2ECE0", "selection": "CFE0FF", "line_nr": "6E7480",
    "line_nr_caret": "0D0F12", "indent": "E3DDD0", "indent_sel": "C2BBAE", "whitespace": "CEC7B8",
    "popup": "FCF9F2", "fold_bg": "E8E2D4", "fold_fg": "3B424E", "search": "FDE7A6",
    "search_stripe": "D9A21B", "text_search": "D7F0F5", "under_caret": "E2E8F5",
    "under_caret_write": "F4DCE6", "brace": "D4DCF2", "inlay_fg": "434A57", "inlay_bg": "EBE5D8",
    "template_bg": "F4EFE4", "added": "15803D", "modified": "1D4ED8", "deleted": "5C6470",
    "error": "DC2626", "warning": "B45309", "weak_warning": "C9A648", "typo": "15803D",
    "link": "1D4ED8", "todo": "0E7490", "unused": "5C6470", "hint_bg": "EFE9DC",
    "diff_ins": "DCF5E3", "diff_mod": "DDE7FF", "diff_del": "E8E3D7", "diff_conf": "FDE7C9",
    "breakpoint": "FBE0E3", "exec": "D9E6FF",
    "console_sys": "323842",
    "term_block_start": "F3EDE1", "term_sel_bg": "E4EDFE",
    "term_hover_start": "0000000C", "term_hover_end": "00000004",
    "ansi": ["0D0F12", "B91C1C", "15803D", "92400E", "1D4ED8", "6D28D9", "0E7490", "262B33",
             "373E4A", "DC2626", "16A34A", "B45309", "2563EB", "7C3AED", "0891B2", "0D0F12"],
    "ansi_bg": ["EAE4D7", "FAD4D6", "D1F0DB", "F7E3B5", "D4E3FC", "E9D8FD", "CCF0F5", "E5DFD2",
                "D8D1C2", "F8B4B8", "B6E8C7", "F5D487", "BBD3FB", "D9BFFC", "AFE5EE", "FAF6EE"],
}


# ---------------------------------------------------------------------------
# Arayüz teması (Islands kalıtımı ile özgün tema dosyası)
# ---------------------------------------------------------------------------

def renk_haritasi_uret(rampa, semantik):
    renkler = {}
    for aile, degerler in rampa.items():
        for i in range(len(degerler) - 1, -1, -1):
            renkler[f"{aile}-{(i + 1) * 10}"] = degerler[i]
    renkler.update(semantik)
    return renkler


def tema_uret(ebeveyn_tema, rampa, semantik, ui_ek, ad, koyu, sema_yolu):
    return {
        "name": ad,
        "dark": koyu,
        "author": "saffetoge",
        "parentTheme": ebeveyn_tema,
        "editorScheme": sema_yolu,
        "colors": renk_haritasi_uret(rampa, semantik),
        "ui": ui_ek,
    }


# ---------------------------------------------------------------------------
# Editör şeması
# ---------------------------------------------------------------------------

def nitelik(fg=None, bg=None, font=None, efekt=None, efekt_tipi=None, serit=None):
    return {k: v for k, v in {
        "FOREGROUND": fg, "BACKGROUND": bg, "FONT_TYPE": font,
        "EFFECT_COLOR": efekt, "EFFECT_TYPE": efekt_tipi, "ERROR_STRIPE_COLOR": serit,
    }.items() if v is not None}


def sema_uret(p):
    renk = {
        "CARET_COLOR": p["caret"], "CARET_ROW_COLOR": p["caret_row"],
        "SELECTION_BACKGROUND": p["selection"], "SELECTION_FOREGROUND": "",
        "LINE_NUMBERS_COLOR": p["line_nr"], "LINE_NUMBER_ON_CARET_ROW_COLOR": p["line_nr_caret"],
        "EDITOR_GUTTER_BACKGROUND": p["bg"], "GUTTER_BACKGROUND": p["bg"],
        "INDENT_GUIDE": p["indent"], "SELECTED_INDENT_GUIDE": p["indent_sel"],
        "VISUAL_INDENT_GUIDE": p["indent"], "MATCHED_BRACES_INDENT_GUIDE_COLOR": p["indent_sel"],
        "RIGHT_MARGIN_COLOR": p["indent"], "METHOD_SEPARATORS_COLOR": p["indent"],
        "TEARLINE_COLOR": p["indent"], "SELECTED_TEARLINE_COLOR": p["indent_sel"],
        "WHITESPACES": p["whitespace"], "SOFT_WRAP_SIGN_COLOR": p["whitespace"],
        "CONSOLE_BACKGROUND_KEY": p["bg"], "DOCUMENTATION_COLOR": p["popup"],
        "BLOCK_TERMINAL_DEFAULT_BACKGROUND": p["bg"], "BLOCK_TERMINAL_DEFAULT_FOREGROUND": p["fg"],
        "BLOCK_TERMINAL_BLOCK_BACKGROUND_START": p["term_block_start"],
        "BLOCK_TERMINAL_BLOCK_BACKGROUND_END": p["bg"],
        "BLOCK_TERMINAL_SELECTED_BLOCK_BACKGROUND": p["term_sel_bg"],
        "BLOCK_TERMINAL_SELECTED_BLOCK_STROKE_COLOR": p["modified"],
        "BLOCK_TERMINAL_HOVERED_BLOCK_BACKGROUND_START": p["term_hover_start"],
        "BLOCK_TERMINAL_HOVERED_BLOCK_BACKGROUND_END": p["term_hover_end"],
        "BLOCK_TERMINAL_INACTIVE_SELECTED_BLOCK_BACKGROUND": p["fold_bg"],
        "BLOCK_TERMINAL_INACTIVE_SELECTED_BLOCK_STROKE_COLOR": p["indent_sel"],
        "BLOCK_TERMINAL_ERROR_BLOCK_STROKE_COLOR": p["error"],
        "BLOCK_TERMINAL_PROMPT_SEPARATOR_COLOR": p["indent"],
        "BLOCK_TERMINAL_GENERATE_COMMAND_PLACEHOLDER_FOREGROUND": p["comment"],
        "BLOCK_TERMINAL_GENERATE_COMMAND_CARET_COLOR": p["caret"],
        "LOOKUP_COLOR": p["popup"], "INFORMATION_HINT": p["hint_bg"], "QUESTION_HINT": p["hint_bg"],
        "ERROR_HINT": p["breakpoint"], "HINT_BORDER": p["indent_sel"],
        "FOLDED_TEXT_BORDER_COLOR": p["fold_bg"], "RECENT_LOCATIONS_SELECTION": p["caret_row"],
        "ADDED_LINES_COLOR": p["added"], "MODIFIED_LINES_COLOR": p["modified"],
        "DELETED_LINES_COLOR": p["deleted"], "WHITESPACES_MODIFIED_LINES_COLOR": p["whitespace"],
        "IGNORED_ADDED_LINES_BORDER_COLOR": p["added"],
        "IGNORED_MODIFIED_LINES_BORDER_COLOR": p["modified"],
        "IGNORED_DELETED_LINES_BORDER_COLOR": p["deleted"],
        "ANNOTATIONS_COLOR": p["comment"], "ANNOTATIONS_LAST_COMMIT_COLOR": p["fg"],
        "DOC_COMMENT_GUIDE": p["indent_sel"], "DOC_COMMENT_LINK": p["link"],
        "FILESTATUS_ADDED": p["added"], "FILESTATUS_MODIFIED": p["modified"],
        "FILESTATUS_DELETED": p["deleted"], "FILESTATUS_UNKNOWN": p["error"],
        "FILESTATUS_IDEA_FILESTATUS_IGNORED": p["number"], "FILESTATUS_RENAMED": p["modified"],
        "NOTIFICATION_BACKGROUND": p["hint_bg"], "PROMOTION_PANE": p["hint_bg"],
    }

    k = p
    a = {
        "TEXT": nitelik(fg=k["fg"], bg=k["bg"]),
        "IDENTIFIER_UNDER_CARET_ATTRIBUTES": nitelik(bg=k["under_caret"], serit=k["under_caret"]),
        "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": nitelik(bg=k["under_caret_write"], serit=k["under_caret_write"]),
        "SEARCH_RESULT_ATTRIBUTES": nitelik(bg=k["search"], serit=k["search_stripe"]),
        "WRITE_SEARCH_RESULT_ATTRIBUTES": nitelik(bg=k["under_caret_write"], serit=k["search_stripe"]),
        "TEXT_SEARCH_RESULT_ATTRIBUTES": nitelik(bg=k["text_search"], serit=k["function"]),
        "MATCHED_BRACE_ATTRIBUTES": nitelik(bg=k["brace"], font=KALIN),
        "UNMATCHED_BRACE_ATTRIBUTES": nitelik(fg=k["error"], efekt=k["error"], efekt_tipi=DALGA),
        "MATCHED_TAG_NAME": nitelik(bg=k["brace"]),
        "FOLDED_TEXT_ATTRIBUTES": nitelik(fg=k["fold_fg"], bg=k["fold_bg"]),
        "INLAY_DEFAULT": nitelik(fg=k["inlay_fg"], bg=k["inlay_bg"]),
        "INLAY_TEXT_WITHOUT_BACKGROUND": nitelik(fg=k["inlay_fg"]),
        "INLINE_PARAMETER_HINT": nitelik(fg=k["inlay_fg"], bg=k["inlay_bg"]),
        "INLINE_PARAMETER_HINT_CURRENT": nitelik(fg=k["fg"], bg=k["brace"]),
        "INLINE_PARAMETER_HINT_HIGHLIGHTED": nitelik(fg=k["fg"], bg=k["brace"]),
        "HYPERLINK_ATTRIBUTES": nitelik(fg=k["link"], efekt=k["link"], efekt_tipi=ALT_CIZGI),
        "FOLLOWED_HYPERLINK_ATTRIBUTES": nitelik(fg=k["type"], efekt=k["type"], efekt_tipi=ALT_CIZGI),
        "CTRL_CLICKABLE": nitelik(fg=k["link"], efekt=k["link"], efekt_tipi=ALT_CIZGI),
        "LIVE_TEMPLATE_ATTRIBUTES": nitelik(efekt=k["caret"]),
        "BREAKPOINT_ATTRIBUTES": nitelik(bg=k["breakpoint"], serit=k["error"]),
        "EXECUTIONPOINT_ATTRIBUTES": nitelik(bg=k["exec"]),
        "INJECTED_LANGUAGE_FRAGMENT": nitelik(bg=k["template_bg"]),
        "DEFAULT_TEMPLATE_LANGUAGE_COLOR": nitelik(bg=k["template_bg"]),
        "TODO_DEFAULT_ATTRIBUTES": nitelik(fg=k["todo"], font=KALIN | ITALIK, serit=k["todo"]),

        # Hata / uyarı
        "ERRORS_ATTRIBUTES": nitelik(efekt=k["error"], efekt_tipi=DALGA, serit=k["error"]),
        "WRONG_REFERENCES_ATTRIBUTES": nitelik(fg=k["error"]),
        "WARNING_ATTRIBUTES": nitelik(efekt=k["warning"], efekt_tipi=DALGA, serit=k["warning"]),
        "INFO_ATTRIBUTES": nitelik(efekt=k["weak_warning"], efekt_tipi=DALGA),
        "RUNTIME_ERROR": nitelik(efekt=k["error"], efekt_tipi=DALGA, serit=k["error"]),
        "DEPRECATED_ATTRIBUTES": nitelik(efekt=k["fg"], efekt_tipi=USTU_CIZILI),
        "MARKED_FOR_REMOVAL_ATTRIBUTES": nitelik(efekt=k["error"], efekt_tipi=USTU_CIZILI),
        "NOT_USED_ELEMENT_ATTRIBUTES": nitelik(fg=k["unused"]),
        "TYPO": nitelik(efekt=k["typo"], efekt_tipi=DALGA),
        "BAD_CHARACTER": nitelik(efekt=k["error"], efekt_tipi=DALGA),

        # Genel dil varsayılanları
        "DEFAULT_KEYWORD": nitelik(fg=k["keyword"]),
        "DEFAULT_IDENTIFIER": nitelik(fg=k["fg"]),
        "DEFAULT_STRING": nitelik(fg=k["string"]),
        "DEFAULT_VALID_STRING_ESCAPE": nitelik(fg=k["escape"]),
        "DEFAULT_INVALID_STRING_ESCAPE": nitelik(fg=k["error"], efekt=k["error"], efekt_tipi=DALGA),
        "DEFAULT_NUMBER": nitelik(fg=k["number"]),
        "DEFAULT_LINE_COMMENT": nitelik(fg=k["comment"], font=ITALIK),
        "DEFAULT_BLOCK_COMMENT": nitelik(fg=k["comment"], font=ITALIK),
        "DEFAULT_DOC_COMMENT": nitelik(fg=k["comment"], font=ITALIK),
        "DEFAULT_DOC_COMMENT_TAG": nitelik(fg=k["doc_tag"], font=ITALIK),
        "DEFAULT_DOC_COMMENT_TAG_VALUE": nitelik(fg=k["class"], font=ITALIK),
        "DEFAULT_DOC_MARKUP": nitelik(fg=k["comment"]),
        "DEFAULT_OPERATION_SIGN": nitelik(fg=k["operator"]),
        "DEFAULT_BRACES": nitelik(fg=k["punct"]),
        "DEFAULT_BRACKETS": nitelik(fg=k["punct"]),
        "DEFAULT_PARENTHS": nitelik(fg=k["punct"]),
        "DEFAULT_COMMA": nitelik(fg=k["punct"]),
        "DEFAULT_SEMICOLON": nitelik(fg=k["punct"]),
        "DEFAULT_DOT": nitelik(fg=k["punct"]),
        "DEFAULT_CLASS_NAME": nitelik(fg=k["class"]),
        "DEFAULT_CLASS_REFERENCE": nitelik(fg=k["class"]),
        "DEFAULT_INTERFACE_NAME": nitelik(fg=k["type"], font=ITALIK),
        "DEFAULT_FUNCTION_DECLARATION": nitelik(fg=k["function"]),
        "DEFAULT_FUNCTION_CALL": nitelik(fg=k["function"]),
        "DEFAULT_INSTANCE_METHOD": nitelik(fg=k["function"]),
        "DEFAULT_STATIC_METHOD": nitelik(fg=k["function"], font=ITALIK),
        "DEFAULT_LOCAL_VARIABLE": nitelik(fg=k["variable"]),
        "DEFAULT_REASSIGNED_LOCAL_VARIABLE": nitelik(fg=k["variable"]),
        "DEFAULT_PARAMETER": nitelik(fg=k["variable"]),
        "DEFAULT_REASSIGNED_PARAMETER": nitelik(fg=k["variable"]),
        "DEFAULT_GLOBAL_VARIABLE": nitelik(fg=k["variable"], font=ITALIK),
        "DEFAULT_INSTANCE_FIELD": nitelik(fg=k["field"]),
        "DEFAULT_STATIC_FIELD": nitelik(fg=k["field"], font=ITALIK),
        "DEFAULT_CONSTANT": nitelik(fg=k["number"], font=ITALIK),
        "DEFAULT_PREDEFINED_SYMBOL": nitelik(fg=k["number"]),
        "DEFAULT_METADATA": nitelik(fg=k["metadata"]),
        "DEFAULT_LABEL": nitelik(fg=k["keyword"]),
        "DEFAULT_TAG": nitelik(fg=k["html_tag"]),
        "DEFAULT_ATTRIBUTE": nitelik(fg=k["attr"]),
        "DEFAULT_ENTITY": nitelik(fg=k["number"]),

        # PHP
        "PHP_KEYWORD": nitelik(fg=k["keyword"], font=k.get("php_keyword_font")),
        "PHP_PRIMITIVE_TYPE_HINT": nitelik(fg=k["keyword"], font=k.get("php_keyword_font")),
        "PHP_MARKUP_ID": nitelik(fg=k["php_tag"], font=KALIN),
        "PHP_TAG": nitelik(fg=k["php_tag"], font=KALIN),
        "PHP_SCRIPTING_BACKGROUND": nitelik(font=k.get("php_scripting_font")),
        "PHP_VAR": nitelik(fg=k["variable"]),
        "PHP_VAR_VAR": nitelik(fg=k["variable"], font=KALIN),
        "PHP_THIS_VAR": nitelik(fg=k["variable"], font=ITALIK),
        "PHP_PARAMETER": nitelik(fg=k["variable"]),
        "PHP_INSTANCE_FIELD": nitelik(fg=k["field"]),
        "PHP_PRIVATE_INSTANCE_FIELD": nitelik(fg=k["field"]),
        "PHP_PROTECTED_INSTANCE_FIELD": nitelik(fg=k["field"]),
        "PHP_STATIC_FIELD": nitelik(fg=k["field"], font=ITALIK),
        "PHP_CONSTANT": nitelik(fg=k["number"], font=ITALIK),
        "PHP_FUNCTION": nitelik(fg=k["function"]),
        "PHP_FUNCTION_CALL": nitelik(fg=k["function"]),
        "PHP_INSTANCE_METHOD": nitelik(fg=k["function"]),
        "PHP_PRIVATE_INSTANCE_METHOD": nitelik(fg=k["function"]),
        "PHP_PROTECTED_INSTANCE_METHOD": nitelik(fg=k["function"]),
        "PHP_STATIC_METHOD": nitelik(fg=k["function"], font=ITALIK),
        "PHP_CLASS": nitelik(fg=k["class"]),
        "PHP_INTERFACE": nitelik(fg=k["type"], font=ITALIK),
        "PHP_ALIAS_REFERENCE": nitelik(fg=k["class"], font=ITALIK),
        "PHP_NAMED_ARGUMENT": nitelik(fg=k["named_arg"]),
        "PHP_ATTRIBUTE": nitelik(fg=k["metadata"]),
        "PHP_STRING": nitelik(fg=k["string"]),
        "PHP_NUMBER": nitelik(fg=k["number"]),
        "PHP_COMMENT": nitelik(fg=k["comment"], font=ITALIK),
        "PHP_DOC_COMMENT_ID": nitelik(fg=k["comment"], font=ITALIK),
        "PHP_DOC_TAG": nitelik(fg=k["doc_tag"], font=ITALIK),
        "PHP_DOC_IDENTIFIER": nitelik(fg=k["class"], font=ITALIK),
        "PHP_DOC_PARAMETER": nitelik(fg=k["variable"], font=ITALIK),
        "PHP_DOC_VAR": nitelik(fg=k["variable"], font=ITALIK),
        "DOC_TEMPLATE_PARAMETER": nitelik(fg=k["type"], font=ITALIK),
        "PHP_HEREDOC_ID": nitelik(fg=k["keyword"]),
        "PHP_HEREDOC_CONTENT": nitelik(fg=k["string"]),
        "PHP_ESCAPE_SEQUENCE": nitelik(fg=k["escape"]),
        "PHP_INVALID_ESCAPE_SEQUENCE": nitelik(fg=k["error"], efekt=k["error"], efekt_tipi=DALGA),
        "PHP_EXEC_COMMAND_ID": nitelik(fg=k["string"]),
        "PHP_OPERATION_SIGN": nitelik(fg=k["operator"]),
        "PHP_CONCATENATION": nitelik(fg=k["operator"]),
        "PHP_BRACKETS": nitelik(fg=k["punct"]),
        "PHP_PARENTHESES": nitelik(fg=k["punct"]),
        "PHP_COMMA": nitelik(fg=k["punct"]),
        "PHP_SEMICOLON": nitelik(fg=k["punct"]),
        "PHP_IDENTIFIER": nitelik(fg=k["fg"]),

        # HTML / XML / Blade
        "HTML_TAG": nitelik(fg=k["punct"]),
        "HTML_TAG_NAME": nitelik(fg=k["html_tag"]),
        "HTML_CUSTOM_TAG_NAME": nitelik(fg=k["class"]),
        "HTML_ATTRIBUTE_NAME": nitelik(fg=k["attr"]),
        "HTML_ATTRIBUTE_VALUE": nitelik(fg=k["string"]),
        "HTML_ENTITY_REFERENCE": nitelik(fg=k["number"]),
        "XML_TAG": nitelik(fg=k["punct"]),
        "XML_TAG_NAME": nitelik(fg=k["html_tag"]),
        "XML_CUSTOM_TAG_NAME": nitelik(fg=k["class"]),
        "XML_ATTRIBUTE_NAME": nitelik(fg=k["attr"]),
        "XML_ATTRIBUTE_VALUE": nitelik(fg=k["string"]),
        "XML_ENTITY_REFERENCE": nitelik(fg=k["number"]),
        "XML_PROLOGUE": nitelik(fg=k["comment"]),

        # CSS / JS küçük dokunuşlar
        "CSS.PROPERTY_NAME": nitelik(fg=k["function"]),
        "CSS.PROPERTY_VALUE": nitelik(fg=k["fg"]),
        "CSS.IDENT": nitelik(fg=k["class"]),
        "CSS.COLOR": nitelik(fg=k["number"]),
        "CSS.URL": nitelik(fg=k["string"]),
        "JS.REGEXP": nitelik(fg=k["escape"]),

        # Konsol ve Terminal
        "CONSOLE_NORMAL_OUTPUT": nitelik(fg=k["fg"]),
        "CONSOLE_ERROR_OUTPUT": nitelik(fg=k["error"]),
        "CONSOLE_SYSTEM_OUTPUT": nitelik(fg=k["console_sys"]),
        "CONSOLE_USER_INPUT": nitelik(fg=k["string"], font=ITALIK),
        "LOG_ERROR_OUTPUT": nitelik(fg=k["error"]),
        "LOG_WARNING_OUTPUT": nitelik(fg=k["warning"]),
        "LOG_INFO_OUTPUT": nitelik(fg=k["fg"]),
        "LOG_VERBOSE_OUTPUT": nitelik(fg=k["console_sys"]),
        "LOG_DEBUG_OUTPUT": nitelik(fg=k["function"]),
        "LOG_EXPIRED_ENTRY": nitelik(fg=k["console_sys"]),
        "TERMINAL_COMMAND_TO_RUN_USING_IDE": nitelik(bg=k["diff_ins"]),
        "BLOCK_TERMINAL_COMMAND": nitelik(fg=k["fg"], font=KALIN),
        "BLOCK_TERMINAL_SEARCH_ENTRY": nitelik(fg=k["fg"], bg=k["search"]),
        "BLOCK_TERMINAL_CURRENT_SEARCH_ENTRY": nitelik(fg=k["fg"], bg=k["text_search"]),
        "BLOCK_TERMINAL_GENERATE_COMMAND_PROMPT_TEXT": nitelik(fg=k["keyword"]),

        # Diff
        "DIFF_INSERTED": nitelik(bg=k["diff_ins"], serit=k["added"]),
        "DIFF_MODIFIED": nitelik(bg=k["diff_mod"], serit=k["modified"]),
        "DIFF_DELETED": nitelik(bg=k["diff_del"], serit=k["deleted"]),
        "DIFF_CONFLICT": nitelik(bg=k["diff_conf"], serit=k["warning"]),
    }

    ansi_adlari = ["BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "GRAY",
                   "DARKGRAY", "RED_BRIGHT", "GREEN_BRIGHT", "YELLOW_BRIGHT", "BLUE_BRIGHT",
                   "MAGENTA_BRIGHT", "CYAN_BRIGHT", "WHITE"]
    block_adlari = ["BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
                    "BLACK_BRIGHT", "RED_BRIGHT", "GREEN_BRIGHT", "YELLOW_BRIGHT", "BLUE_BRIGHT",
                    "MAGENTA_BRIGHT", "CYAN_BRIGHT", "WHITE_BRIGHT"]
    for konsol_ad, blok_ad, fg_deger, bg_deger in zip(ansi_adlari, block_adlari, k["ansi"], k["ansi_bg"]):
        a[f"CONSOLE_{konsol_ad}_OUTPUT"] = nitelik(fg=fg_deger, bg=bg_deger)
        a[f"BLOCK_TERMINAL_{blok_ad}"] = nitelik(fg=fg_deger, bg=bg_deger)

    return renk, a


def sema_xml(p):
    renk, nitelikler = sema_uret(p)
    satirlar = [
        f'<scheme name="{escape(p["ad"])}" version="142" parent_scheme="{p["ebeveyn"]}">',
        "  <metaInfo>",
        '    <property name="ide">PhpStorm</property>',
        '    <property name="ideVersion">2026.2.0.0</property>',
        "  </metaInfo>",
        "  <colors>",
    ]
    for ad in sorted(renk):
        satirlar.append(f'    <option name="{ad}" value="{renk[ad]}" />')
    satirlar += ["  </colors>", "  <attributes>"]
    for ad in sorted(nitelikler):
        degerler = nitelikler[ad]
        if not degerler:
            satirlar.append(f'    <option name="{ad}">\n      <value />\n    </option>')
            continue
        satirlar.append(f'    <option name="{ad}">')
        satirlar.append("      <value>")
        for anahtar, deger in degerler.items():
            satirlar.append(f'        <option name="{anahtar}" value="{deger}" />')
        satirlar.append("      </value>")
        satirlar.append("    </option>")
    satirlar += ["  </attributes>", "</scheme>", ""]
    return "\n".join(satirlar)


# ---------------------------------------------------------------------------
# Eklenti tanımı (JetBrains Marketplace uyumlu)
# ---------------------------------------------------------------------------

PLUGIN_XML = f"""<idea-plugin require-restart="true">
  <id>com.saffetoge.sotheme</id>
  <name>SOTheme</name>
  <version>{SURUM}</version>
  <vendor url="https://github.com/saffetoge" email="saffetoge@gmail.com">saffetoge</vendor>
  <description><![CDATA[
    <p>Dark and light Islands UI themes with syntax color schemes for PHP, Blade, HTML, CSS, and JavaScript.</p>
    <ul>
      <li><b>SOTheme Dark</b>: deep navy workspace with violet accents, balanced contrast, and tailored terminal colors.</li>
      <li><b>SOTheme Light</b>: warm cream workspace with high-contrast dark text and readable terminal ANSI colors.</li>
    </ul>
    <p>Built on top of the Islands UI architecture (<code>Islands Dark</code> and <code>Islands Light</code>) for clean visual hierarchy across editor tabs, tool windows, diffs, and the block terminal.</p>
    <p><b>Türkçe:</b> Islands arayüzü üzerine kurulu SOTheme Dark (lacivert zemin, mor vurgu) ve SOTheme Light (sıcak krem zemin, yüksek kontrast) tema ailesi; PHP, Blade, HTML, CSS ve terminal için özel renk şemaları içerir.</p>
  ]]></description>
  <change-notes><![CDATA[
    <ul>
      <li><b>1.2.0</b>: Switched to native <code>Islands Dark</code> and <code>Islands Light</code> parent theme inheritance for full compatibility with 2026.2 and 2026.3+ IDEs.</li>
      <li>Added <code>require-restart="true"</code> to prevent dynamic theme unload class loader leaks (IJPL-261778).</li>
      <li>Updated plugin icon, English description, and Marketplace metadata.</li>
    </ul>
  ]]></change-notes>
  <idea-version since-build="262"/>
  <depends>com.intellij.modules.platform</depends>
  <extensions defaultExtensionNs="com.intellij">
    <themeProvider id="com.saffetoge.sotheme.dark" path="/themes/SOTheme_Dark.theme.json"/>
    <themeProvider id="com.saffetoge.sotheme.light" path="/themes/SOTheme_Light.theme.json"/>
  </extensions>
</idea-plugin>
"""

IKON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
  <defs>
    <linearGradient id="so-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#141927"/>
      <stop offset="1" stop-color="#0A0D16"/>
    </linearGradient>
    <linearGradient id="so-frame" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#8B5CF6"/>
      <stop offset="1" stop-color="#2563EB"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="36" height="36" rx="9" fill="url(#so-bg)" stroke="url(#so-frame)" stroke-width="1.5"/>
  <rect x="6.5" y="6.5" width="18.5" height="18.5" rx="4.5" fill="#1A2030" stroke="#8B5CF6" stroke-width="1.2"/>
  <rect x="9.5" y="10.5" width="6.5" height="2" rx="1" fill="#C4B5FD"/>
  <rect x="9.5" y="14.5" width="10.5" height="2" rx="1" fill="#5EEAD4"/>
  <rect x="11.5" y="18.5" width="8.5" height="2" rx="1" fill="#B9E57A"/>
  <rect x="15" y="15" width="18.5" height="18.5" rx="4.5" fill="#FAF6EE" stroke="#2563EB" stroke-width="1.2"/>
  <rect x="18" y="19" width="6.5" height="2" rx="1" fill="#6D28D9"/>
  <rect x="18" y="23" width="10.5" height="2" rx="1" fill="#1D4ED8"/>
  <rect x="20" y="27" width="8.5" height="2" rx="1" fill="#15803D"/>
</svg>
"""


def main():
    shutil.rmtree(SRC, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)
    (SRC / "META-INF").mkdir(parents=True)
    (SRC / "themes").mkdir()
    DIST.mkdir()

    temalar = {
        "SOTheme_Dark": tema_uret(
            "Islands Dark", KOYU_RAMPA, KOYU_SEMANTIK, KOYU_UI_EK,
            "SOTheme Dark", True, "/themes/SOTheme_Dark.xml",
        ),
        "SOTheme_Light": tema_uret(
            "Islands Light", ACIK_RAMPA, ACIK_SEMANTIK, ACIK_UI_EK,
            "SOTheme Light", False, "/themes/SOTheme_Light.xml",
        ),
    }
    for dosya, tema in temalar.items():
        (SRC / "themes" / f"{dosya}.theme.json").write_text(
            json.dumps(tema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for dosya, palet in (("SOTheme_Dark", KOYU), ("SOTheme_Light", ACIK)):
        xml = sema_xml(palet)
        (SRC / "themes" / f"{dosya}.xml").write_text(xml, encoding="utf-8")
        (DIST / f"{dosya}.icls").write_text(xml, encoding="utf-8")

    (SRC / "META-INF" / "plugin.xml").write_text(PLUGIN_XML, encoding="utf-8")
    (SRC / "META-INF" / "pluginIcon.svg").write_text(IKON_SVG, encoding="utf-8")

    lisans = KOK / "LICENSE"
    if lisans.exists():
        (SRC / "META-INF" / "LICENSE").write_text(lisans.read_text(encoding="utf-8"), encoding="utf-8")

    jar = DIST / f"SOTheme-{SURUM}.jar"
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\r\n\r\n")
        for yol in sorted(SRC.rglob("*")):
            if yol.is_file():
                z.write(yol, yol.relative_to(SRC).as_posix())

    print(f"Hazır: {jar.relative_to(KOK)}")
    for yol in sorted(DIST.glob("*.icls")):
        print(f"       {yol.relative_to(KOK)}")


if __name__ == "__main__":
    main()
