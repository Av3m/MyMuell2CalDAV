import http.client
import json
import databinding.LocalDataStorage as LocalDataStorage
import logging
import re

class MyMuellDataModel(object):
    MyMuellHost = 'mymuell.jumomind.com'
    log = logging.getLogger("MyMuellDataModel")

    def __init__(self):
        self.client = http.client.HTTPSConnection(MyMuellDataModel.MyMuellHost)

        self.storage = LocalDataStorage.LocalDataStorage()
        self.cities = self.__get_cities()

    def get_cities_by_request(self):
        self.client.request('GET', '/mmapp/loxone/lox.php?r=cities')
        response = self.client.getresponse()
        return json.loads(str(response.read(), encoding='utf-8'))

    def get_events(self, city_id, area_id):
        self.client.request('GET', '/mmapp/loxone/lox.php?r=dates/0&city_id={city_id}&area_id={area_id}'.format(city_id=city_id, area_id=area_id))
        response = self.client.getresponse()
        ret = str(response.read(), encoding='utf-8')
        return json.loads(ret)

    def __get_cities(self):
        cities = self.storage.city_data
        if cities is not None:
            MyMuellDataModel.log.debug("using stored values")
            return cities
        else:
            cities = self.get_cities_by_request()
            self.storage.city_data = cities

        return cities

    def get_city_names(self, indices):
        ret = []
        for idx in indices:
            e = self.get_city_by_index(idx)
            if e is not None:
                ret.append(e["name"])
        return ret

    def match_city(self, pattern):
        ret = []

        n = 0
        for i in self.cities:

            m = re.search(pattern, i["name"], re.IGNORECASE)
            if m is not None:
                ret.append(n)
            n = n + 1

        return ret

    def get_city_by_index(self, idx):
        if len(self.cities) < idx:
            return None

        return self.cities[idx]

    def get_city_by_id(self, id):
        for i in self.cities:
            if i["id"] == id:
                return i

        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    model = MyMuellDataModel()
    matches = model.match_city("eich")
