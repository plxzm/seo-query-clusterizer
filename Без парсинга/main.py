import pandas as pd
print('Введите порог кластеризации')
porog = int(input())
print('Введите количество url для запроса (уровень ТОПа)')
top = int(input())
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
            # Сцепляем значения списка с запятой в виде разделителя
            tik = ', '.join(inter)
            # Записываем полученные значения в словарь для каждого ключа
            key_indices[key] = [index, tik]      
            
    return key_indices

def create_dict_from_excel(filepath):
    # Импортируем таблицу из excel файла
    df = pd.read_excel(filepath)
    # Создаем словарь
    dictionary = {}
    # Проходим по каждой пачке строк таблицы (глубине топа)
    for i in range(0, len(df), top):
        key = df.iloc[i, 0]
        # Объединяем 10 строк второго столбца
        values = list(df.iloc[i : i+top, 1])
        dictionary[key] = values
    return dictionary


filepath = 'data.xlsx'
dictionary = create_dict_from_excel(filepath)
final = assign_index(dictionary)

# Из полученного словаря создаем датафрейм
res = pd.DataFrame.from_dict(final)
# Задаем названия индексам (в будущем столбцам)
ff = res.set_index(pd.Index(['Группа', 'Пересечения']))
# Транспонируем и сохраняем в excel файл 
ff.T.to_excel('output.xlsx')