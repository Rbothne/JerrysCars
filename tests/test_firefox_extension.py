import importlib.util
import json
import pathlib
import unittest

EXTENSION = pathlib.Path(__file__).parent.parent / "extension"
spec = importlib.util.spec_from_file_location("make_firefox", EXTENSION / "make_firefox.py")
make_firefox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_firefox)


class FirefoxCopy(unittest.TestCase):
    def test_the_firefox_copy_is_the_same_scripts_as_the_chrome_one(self):
        for name in make_firefox.FILES:
            self.assertEqual((make_firefox.TARGET / name).read_bytes(), (make_firefox.SOURCE / name).read_bytes(),
                             f"{name} is out of date: run py extension/make_firefox.py")

    def test_the_firefox_manifest_is_the_one_the_script_writes(self):
        self.assertEqual((make_firefox.TARGET / "manifest.json").read_text(encoding="utf-8"), make_firefox.manifest(),
                         "manifest.json is out of date: run py extension/make_firefox.py")

    def test_firefox_gets_an_event_page_an_id_and_the_page_world_it_needs(self):
        made = json.loads(make_firefox.manifest())
        self.assertEqual(made["background"], {"scripts": ["capture.js", "background.js"]})
        gecko = made["browser_specific_settings"]["gecko"]
        self.assertRegex(gecko["id"], r"^[a-zA-Z0-9-._]*@[a-zA-Z0-9-._]+$")
        self.assertEqual((gecko["strict_min_version"], gecko["data_collection_permissions"]), ("128.0", {"required": ["websiteContent"]}))
        self.assertEqual([script.get("world") for script in made["content_scripts"]], ["MAIN", None])
        self.assertNotIn("minimum_chrome_version", made)

    def test_the_chrome_manifest_keeps_its_service_worker(self):
        chrome = json.loads((make_firefox.SOURCE / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(chrome["background"], {"service_worker": "background.js"})


if __name__ == "__main__":
    unittest.main()
