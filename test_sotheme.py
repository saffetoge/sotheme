#!/usr/bin/env python3
"""SOTheme paket ve Marketplace uyumluluk doğrulama testleri."""

import json
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import olustur

PHPSTORM_JAR = Path("/Applications/PhpStorm.app/Contents/lib/intellij.platform.ide.impl.jar")


def _duz_ui(ui, on_ek=""):
    sonuc = {}
    for k, v in (ui or {}).items():
        tam = f"{on_ek}.{k}" if on_ek else k
        if isinstance(v, dict):
            sonuc.update(_duz_ui(v, tam))
        else:
            sonuc[tam] = v
    return sonuc


def _renkleri_coz(ham):
    cozulmus = {}

    def al(anahtar, gorulen=None):
        if anahtar in cozulmus:
            return cozulmus[anahtar]
        if gorulen is None:
            gorulen = set()
        if anahtar in gorulen:
            raise AssertionError(f"Döngüsel renk referansı: {anahtar}")
        gorulen.add(anahtar)
        deger = ham[anahtar]
        if isinstance(deger, str) and not deger.startswith("#"):
            if deger not in ham:
                raise AssertionError(f"Tanımsız renk referansı: {anahtar} -> {deger}")
            deger = al(deger, gorulen)
        cozulmus[anahtar] = deger.upper() if isinstance(deger, str) and deger.startswith("#") else deger
        return cozulmus[anahtar]

    for k in ham:
        al(k)
    return cozulmus


class SothemePaketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        olustur.main()
        cls.jar_yolu = olustur.DIST / f"SOTheme-{olustur.SURUM}.jar"

    def test_jar_dosyasi_ve_zorunlu_icerik(self):
        self.assertTrue(self.jar_yolu.exists(), "Eklenti JAR dosyası üretilmedi")
        with zipfile.ZipFile(self.jar_yolu) as z:
            adlar = set(z.namelist())
        beklenen = {
            "META-INF/MANIFEST.MF",
            "META-INF/plugin.xml",
            "META-INF/pluginIcon.svg",
            "META-INF/LICENSE",
            "themes/SOTheme_Dark.theme.json",
            "themes/SOTheme_Dark.xml",
            "themes/SOTheme_Light.theme.json",
            "themes/SOTheme_Light.xml",
        }
        self.assertTrue(beklenen.issubset(adlar), f"Eksik JAR girdileri: {beklenen - adlar}")

    def test_plugin_xml_marketplace_kosullari(self):
        with zipfile.ZipFile(self.jar_yolu) as z:
            kok = ET.fromstring(z.read("META-INF/plugin.xml"))
            jar_adlar = set(z.namelist())

        self.assertEqual(kok.tag, "idea-plugin")
        self.assertEqual(kok.attrib.get("require-restart"), "true")

        eklenti_id = kok.findtext("id")
        self.assertEqual(eklenti_id, "com.saffetoge.sotheme")

        ad = kok.findtext("name")
        self.assertEqual(ad, "SOTheme")
        self.assertLessEqual(len(ad), 30)
        for yasak in ("plugin", "intellij", "jetbrains", "phpstorm"):
            self.assertNotIn(yasak, ad.lower())

        surum = kok.findtext("version")
        self.assertRegex(surum, r"^\d+\.\d+\.\d+$")
        self.assertEqual(surum, olustur.SURUM)

        satici = kok.find("vendor")
        self.assertIsNotNone(satici)
        self.assertTrue((satici.text or "").strip())
        self.assertTrue((satici.attrib.get("url") or "").startswith("https://"))
        self.assertIn("@", satici.attrib.get("email") or "")

        idea_surum = kok.find("idea-version")
        self.assertIsNotNone(idea_surum)
        self.assertEqual(idea_surum.attrib.get("since-build"), "262")
        self.assertNotIn("until-build", idea_surum.attrib)

        aciklama_ham = kok.findtext("description") or ""
        aciklama_duz = re.sub(r"<[^>]+>", " ", aciklama_ham)
        aciklama_duz = re.sub(r"\s+", " ", aciklama_duz).strip()
        self.assertGreaterEqual(len(aciklama_duz), 40)
        ilk_40 = aciklama_duz[:40]
        self.assertTrue(ilk_40.isascii(), f"İlk 40 karakter saf İngilizce olmalı: {ilk_40!r}")

        degisiklik = kok.findtext("change-notes") or ""
        self.assertIn(olustur.SURUM, degisiklik)
        self.assertNotIn("Add change notes here", degisiklik)

        saglayicilar = kok.findall("./extensions/themeProvider")
        self.assertEqual(len(saglayicilar), 2)
        kimlikler = {s.attrib["id"]: s.attrib["path"] for s in saglayicilar}
        self.assertEqual(
            kimlikler,
            {
                "com.saffetoge.sotheme.dark": "/themes/SOTheme_Dark.theme.json",
                "com.saffetoge.sotheme.light": "/themes/SOTheme_Light.theme.json",
            },
        )
        for yol in kimlikler.values():
            self.assertIn(yol.lstrip("/"), jar_adlar)

    def test_ikon_svg_boyut_ve_metinsiz_olma(self):
        with zipfile.ZipFile(self.jar_yolu) as z:
            svg_metin = z.read("META-INF/pluginIcon.svg").decode("utf-8")
        kok = ET.fromstring(svg_metin)
        self.assertEqual(kok.attrib.get("width"), "40")
        self.assertEqual(kok.attrib.get("height"), "40")
        self.assertEqual(kok.attrib.get("viewBox"), "0 0 40 40")
        self.assertNotIn("<text", svg_metin)

    def test_tema_json_kalitimi_ve_ozgunluk(self):
        with zipfile.ZipFile(self.jar_yolu) as z:
            jar_adlar = set(z.namelist())
            koyu = json.loads(z.read("themes/SOTheme_Dark.theme.json"))
            acik = json.loads(z.read("themes/SOTheme_Light.theme.json"))

        self.assertEqual(koyu["parentTheme"], "Islands Dark")
        self.assertTrue(koyu["dark"])
        self.assertEqual(acik["parentTheme"], "Islands Light")
        self.assertFalse(acik["dark"])

        for tema in (koyu, acik):
            self.assertIn(tema["editorScheme"].lstrip("/"), jar_adlar)
            # JetBrains tema kopyası içermemeli (yalnız SOTheme renk ve minimal UI ekleri)
            self.assertNotIn("icons", tema)
            self.assertLess(len(tema["colors"]), 70)
            self.assertLess(len(_duz_ui(tema["ui"])), 15)
            for anahtar, deger in tema["colors"].items():
                self.assertRegex(
                    deger,
                    r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
                    f"Geçersiz hex renk: {anahtar}={deger}",
                )

    def test_editor_sema_xml_ve_icls_gecerliligi(self):
        for dosya in ("SOTheme_Dark", "SOTheme_Light"):
            xml_yolu = olustur.SRC / "themes" / f"{dosya}.xml"
            icls_yolu = olustur.DIST / f"{dosya}.icls"
            self.assertEqual(xml_yolu.read_text(encoding="utf-8"), icls_yolu.read_text(encoding="utf-8"))
            kok = ET.fromstring(xml_yolu.read_text(encoding="utf-8"))
            self.assertEqual(kok.tag, "scheme")
            for opt in kok.findall("./colors/option"):
                deger = opt.attrib["value"]
                if deger == "":
                    self.assertEqual(opt.attrib["name"], "SELECTION_FOREGROUND")
                else:
                    self.assertRegex(deger, r"^[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")

    @unittest.skipUnless(PHPSTORM_JAR.exists(), "PhpStorm kurulu değil")
    def test_phpstorm_islands_ebeveyni_ile_tam_renk_cozumlemesi(self):
        with zipfile.ZipFile(PHPSTORM_JAR) as pz, zipfile.ZipFile(self.jar_yolu) as sz:
            def oku(z, yol):
                return json.loads(re.sub(r"(?m)^\s*//.*$", "", z.read(yol).decode("utf-8")))

            eslesmeler = [
                ("themes/SOTheme_Dark.theme.json", "themes/islands/ManyIslandsDark.theme.json", "themes/expUI/expUI_dark.theme.json"),
                ("themes/SOTheme_Light.theme.json", "themes/islands/ManyIslandsLight.theme.json", "themes/expUI/expUI_light_with_light_header.theme.json"),
            ]
            for sotheme_yol, islands_yol, exp_yol in eslesmeler:
                exp = oku(pz, exp_yol)
                isl = oku(pz, islands_yol)
                so = oku(sz, sotheme_yol)

                birlesik_renk = {**exp.get("colors", {}), **isl.get("colors", {}), **so.get("colors", {})}
                cozulmus = _renkleri_coz(birlesik_renk)

                # SOTheme'in tanımladığı tüm renkler ebeveyn haritasında gerçekten karşılık bulmalı
                for anahtar in so["colors"]:
                    self.assertIn(anahtar, isl["colors"], f"{sotheme_yol}: {anahtar} Islands ebeveyninde yok")

                # Tüm birleşik UI içindeki named color referansları çözülmeli
                birlesik_ui = {**_duz_ui(exp.get("ui")), **_duz_ui(isl.get("ui")), **_duz_ui(so.get("ui"))}
                for ui_anahtar, deger in birlesik_ui.items():
                    if isinstance(deger, str) and re.fullmatch(r"[a-z][a-z0-9-]*", deger) and "-" in deger:
                        if deger not in ("true", "false"):
                            self.assertIn(deger, cozulmus, f"UI tanımsız renk: {ui_anahtar}={deger}")


if __name__ == "__main__":
    unittest.main()
