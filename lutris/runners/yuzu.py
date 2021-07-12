# Standard Library
import filecmp
import os
from gettext import gettext as _
from shutil import copyfile

# Other utils
import requests
import re

# Lutris Modules
from lutris.runners.runner import Runner
from lutris.util import system
from lutris.util.log import logger


class yuzu(Runner):
    human_name = _("Yuzu")
    platforms = [_("Nintendo Switch")]
    description = _("Nintendo Switch emulator")
    runnable_alone = True
    runner_executable = "yuzu/mainline/yuzu"
    game_options = [
        {
            "option": "main_file",
            "type": "file",
            "label": _("ROM file"),
            "help": _("The game data, commonly called a ROM image."),
        }
    ]
    runner_options = [
        {
            "option": "prod_keys",
            "label": _("Encryption keys"),
            "type": "file",
            "help": _("File containing the encryption keys."),
        }, {
            "option": "title_keys",
            "label": _("Title keys"),
            "type": "file",
            "help": _("File containing the title keys."),
        },
        {
            "option": "fullscreen",
            "label": _("Open game in fullscreen"),
            "type": "bool",
            "default": False,
            "help": _("Tells Yuzu to launch the game in fullscreen."),
        }
    ]

    @property
    def yuzu_data_dir(self):
        """Return dir where Yuzu files lie."""
        candidates = ("~/.local/share/yuzu", )
        for candidate in candidates:
            path = system.fix_path_case(os.path.join(os.path.expanduser(candidate), "nand"))
            if path:
                return path[:-len("nand")]

    @property
    def download_url(self):
        """The download URL for Yuzu"""
        githubResponse = requests.get("https://api.github.com/repos/yuzu-emu/yuzu-mainline/releases/latest").json()
        pattern = re.compile("yuzu-linux-(.*).7z")
        linux_version = [x for x in githubResponse["assets"] if pattern.match(x["name"])][0]
        print(linux_version)
        return linux_version["browser_download_url"]
        

    def play(self):
        """Run the game."""
        arguments = [self.get_executable()]
        rom = self.game_config.get("main_file") or ""
        if not system.path_exists(rom):
            return {"error": "FILE_NOT_FOUND", "file": rom}
        if (self.runner_config.get("fullscreen")):
            arguments.append("-f")
        arguments.append("-g")
        arguments.append(rom)
        return {"command": arguments}

    def _update_key(self, key_type):
        """Update a keys file if set """
        yuzu_data_dir = self.yuzu_data_dir
        if not yuzu_data_dir:
            logger.error("Yuzu data dir not set")
            return
        if key_type == "prod_keys":
            key_loc = os.path.join(yuzu_data_dir, "keys/prod.keys")
        elif key_type == "title_keys":
            key_loc = os.path.join(yuzu_data_dir, "keys/title.keys")
        else:
            logger.error("Invalid keys type %s!", key_type)
            return

        key = self.runner_config.get(key_type)
        if not key:
            logger.debug("No %s file was set.", key_type)
            return
        if not system.path_exists(key):
            logger.warning("Keys file %s does not exist!", key)
            return

        keys_dir = os.path.dirname(key_loc)
        if not os.path.exists(keys_dir):
            os.makedirs(keys_dir)
        elif os.path.isfile(key_loc) and filecmp.cmp(key, key_loc):
            # If the files are identical, don't do anything
            return
        copyfile(key, key_loc)

    def prelaunch(self):
        for key in ["prod_keys", "title_keys"]:
            self._update_key(key_type=key)
        return True
