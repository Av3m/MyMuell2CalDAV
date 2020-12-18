from appdirs import *
import json
import os
import re
import copy
from cryptography.fernet import Fernet

class LocalDataStorage(object):
    def __init__(self):
        self.appname = "MyMuellDav"
        self.appauthor = "Av3m"
        self.__fernet = Fernet(b'kWUFurHmtMWX6nOMhpFR45DpuNVPckSQ9t95_ADG2dA=')

        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

    DefaultSettings = {
        'url': '',
        'user': '',
        'password': '',
        'calendar': '',
        'mymuellcity': '',
    }

    @property
    def user_data_dir(self):
        return user_data_dir(self.appname, self.appauthor)

    @property
    def file_settings(self):
        return os.path.join(self.user_data_dir, "settings.json")
    @property
    def file_city_data(self):
        return os.path.join(self.user_data_dir, "city_data.json")

    @property
    def settings(self):
        if os.path.exists(self.file_settings):
            with open(self.file_settings, "r") as f:
                j = json.load(f)
                j["password"] = str(self.__fernet.decrypt(bytes(j["password"], encoding="utf-8")), encoding="utf-8")
                return j
        else:
            return LocalDataStorage.DefaultSettings

    @settings.setter
    def settings(self, val):
        if val is None and os.path.exists(self.file_settings):
            os.remove(self.file_settings)
            return

        with open(self.file_settings, "w+") as f:
            v = copy.copy(val)
            v["password"] = str(self.__fernet.encrypt(bytes(v["password"], encoding="utf-8")), encoding="utf-8")
            json.dump(v, f)

        os.chmod(self.file_settings, 0o0600)

    @property
    def city_data(self):
        if os.path.exists(self.file_city_data):
            with open(self.file_city_data, "r") as f:
                return json.load(f)
        else:
            return None

    @city_data.setter
    def city_data(self, val):
        if val is None and os.path.exists(self.file_city_data):
            os.remove(self.file_city_data)
            return

        with open(self.file_city_data, "w+") as f:
            json.dump(val, f)

