
# выходные данные - массив: на i-e изобр-е - подмассив: найденный объект - подмассив: x,y,x_e,y_e объекта

def make_data_for_test(difficulty) -> list:
    pass

# выходные данные: i-е изобр-е: milliseconds,
#                               количество попаданий (покрытие площади более 50%),
#                               количество false-positive (не попадание или больше чем есть),
#                               количество false-negative (истинное кол-во минус количество попаданий)
#  хинт: попадание искать по ближайшей координате (подсчётом расстояния между левым верхним углом)
#  это будет sqrt((x1-x2)**2+(y1-y2)**2). как только нашли кратчайшее расстояние - считаем попадание
#  считать попадание через проекции (запомни, первая координата - ориг. рамка, вторая - тестируемая рамка
#                                    cначала идут коор-ты левого верхнего края, потом - нижнего правого):
#  i - номер изображения
#  j - номер объекта на тестируемой системе на i-м изображении
#  k = find_index_of_closest(i, j)
#  x1, y1, x1_e, y1_e = valid_data[i, k]
#  true_area = (x1_e - x1) * (y1_e - y1)
#  h = max(min(x1_e, x2_e) - max(x1,x2), 0)
#  w = max(min(y1_e, y2_e) - max(y1,y2), 0)
#  overlap = h * w
#  if overlap / true_area > 0.5:
#       test_data[i, 1] += 1
#   else:
#       test_data[i, 2] += 1
#  test_data[i, 3] = len(valid_data[i]) - test_data[i, 1]

def test_caffe_cnn(path: str, difficulty) -> list:
    return []

def test_darknet_cnn(path: str, difficulty) -> list:
    return []

def test_tensorflow_cnn(path: str, difficulty) -> list:
    return []

def test_tflite_cnn(path: str, difficulty) -> list:
    return []


def print_test_data_to_file(data, name):
    # обязательно В НАЧАЛЕ ФАЙЛА
    # будут средние значения
    pass