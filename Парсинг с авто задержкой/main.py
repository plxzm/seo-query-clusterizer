import time
import pandas as pd
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import requests

with open("config.txt", "r") as file:
    data = file.readlines()
# Извлечение данных LoginAPI и PassAPI
for line in data:
    if "LoginAPI" in line:
        LoginAPI = line.split("=")[1].strip()
    elif "PassAPI" in line:
        PassAPI = line.split("=")[1].strip()

print('Введите порог кластеризации')
porog = int(input())

#Проверка доступных часовых лимитов и автоматическое задание скорости парсинга
now = datetime.now(timezone.utc)
req = requests.get('https://yandex.ru/search/xml?action=limits-info&user=' + LoginAPI + '&key=' + PassAPI)
xml_string = req.content
xml_string = xml_string.decode('utf-8')
root = ET.fromstring(xml_string)
intervals_data = {}
for interval in root.iter('time-interval'):
    from_time = datetime.strptime(interval.attrib['from'], "%Y-%m-%d %H:%M:%S %z")
    to_time = datetime.strptime(interval.attrib['to'], "%Y-%m-%d %H:%M:%S %z")
    period = (from_time, to_time)
    # сохраняем данные в словарь
    if from_time <= now <= to_time:
        hourly_limits = interval.text

# Задание задержки на количество запросов в секунду, подробнее https://yandex.ru/dev/xml/doc/dg/concepts/rps-limits.html
rps_restriction = 2000 / int(hourly_limits)

#Парсинг выдачи по ключевым словам из файла, сохранение их в словарь
from pyyaxml.search import YaSearch
with open("queries.txt", "r", encoding="utf-8") as f:
    queries = f.readlines()
    queries = [query.strip() for query in queries]
y = YaSearch(LoginAPI, PassAPI)
dictionary = {}

for i in range(len(queries)):
    results = y.search(queries[i], page=1)
    key = queries[i]
    urls = list()
    for result in results.items:
        urls.append(result.url)
    dictionary[key] = urls
    # Реализация задержки
    time.sleep(rps_restriction)

# Основная функция выполняющая кластеризацию
def assign_index(dictionary):
    # Создаем словарь для хранения индексов ключей
    key_indices = {}
    # Проходим по всем ключам словаря
    for key in dictionary:
        inter = ()
        # Проверяем, есть ли уже индекс для этого ключа
        if key in key_indices:
            # Если есть, используем его
            index = key_indices[key]
        else:
            # Если нет, проходим по всем ключам с индексом
            for other_key, other_index in key_indices.items():
                # Проверяем количество пересекающихся значений
                common_values = set(dictionary[key]).intersection(set(dictionary[other_key]))
                if len(common_values) >= porog:
                    # Задаем название группы
                    index = other_index[0]
                    # Записываем пересечения между предыдущим и текущим ключом в цикле
                    inter = set(dictionary[key]).intersection(set(dictionary[other_key]))
                    break
            else:
                # Если не нашли подходящий индекс, создаем новый
                index = key
            # Сцепляем значения списка с разделителем в виде запятой
            tik = ', '.join(inter)
            # Записываем полученные значения в словарь для каждого ключа
            key_indices[key] = [index, tik]
    return key_indices

# Формируем итоговый документ
final = assign_index(dictionary)
res = pd.DataFrame.from_dict(final)
# Задаем названия индексам (в будущем столбцам)
ff = res.set_index(pd.Index(['Группа', 'Пересечения']))
# Транспонируем и сохраняем в excel файл
ff.T.to_excel('output.xlsx')