import os

USER_HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(USER_HOME, ".audioPhile")

#python dataclass for config init
class config:

    _defaults = {
        "download_path": CONFIG_PATH,
        "isolated_url": ""
    }

    def __init__(self, download_path: str = None, isolated_url: str = None):
        self.download_path = download_path if download_path is not None else self._defaults["download_path"]
        self.isolated_url = isolated_url if isolated_url is not None else self._defaults["isolated_url"]

    def __repr__(self):
        return f"Config(download_path={self.download_path}, isolated_url={self.isolated_url})"

    def __eq__(self, other):
        if not isinstance(other, config):
            return NotImplemented
        return self.download_path == other.download_path and self.isolated_url == other.isolated_url

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:   
            return NotImplemented
        else:
            return not result

    def __hash__(self):
        return hash((self.download_path, self.isolated_url))

    

