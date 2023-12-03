from math import isnan
from numpy import nan
import pandas as pd


df = pd.read_csv('ecom_raw.csv', sep=',', decimal=".")

# PEP8
df.columns = [x.lower().replace(" ", "_") for x in df.columns]

# столбец “payer” с информацией о том, является ли пользователь платящим или нет
df["payer"] = df["revenue"].apply(lambda x: int(isnan(x)))

# округление длительности сессии (так как все числа очень близки к целому, вероятно ошибка в процессе передачи)
df["sessiondurationsec"] = df["sessiondurationsec"].apply(round)

# добавление столбца с итоговой суммой покупки после промокода 10%
df["final_price"] = df["revenue"]
df.loc[df["promo_code"] == 1, "final_price"] = df.loc[df["promo_code"] == 1, "final_price"].apply(lambda x: round(x * 0.9))

# устранение явных дубликатов
if len(df["user_id"]) != len(list(set(df["user_id"]))):
    df = df.drop_duplicates(subset=["user_id"], ignore_index=True)

# устранение ошибок в категориальных данных
df.loc[df["channel"] == "контексная реклама", "channel"] = "контекстная реклама"
df.loc[df["device"] == "android", "device"] = "Android"
df.loc[df["region"] == "Unjted States", "region"] = "United States"
df.loc[df["region"] == "germany", "region"] = "Germany"
df.loc[df["region"] == "germany", "region"] = "France"
df.loc[df["region"] == "Franсe", "region"] = "France"
df.loc[df["region"] == "Frаnce", "region"] = "France"
df.loc[df["region"] == "Frаncе", "region"] = "France"
df.loc[df["region"] == "UК", "region"] = "UK"


# ТЗ (невыполненные пункты)
# проверить данные на пропуски и заполнить их при необходимости. Обосновать решение.
# перевести тип данных столбцов с датой и временем в соответствующий формат при необходимости (pd.to_datetime())
# определить исследуемый период, весь ли период брать для исследования или нет?
# проверить данные на выбросы и адекватность данных
# добавить столбец с указанием времени суток визита (утро 06:00-09:59, день 10:00-16:59, вечер 17:00-21:59, ночь 22:00-05:59)
# Провести аналитический и графический анализ данных:
# # Доля продаж по регионам
# # Доля продаж по источникам
# # Доля продаж по устройствам
# # Количество пользователей с разбивкой на платящих/не платящих по регионам
# # Количество пользователей с разбивкой на платящих/не платящих по устройствам
# # Количество пользователей с разбивкой на платящих/не платящих по источникам
# # Графики, показывающие есть ли сезонность в продажах по месяцам, дням недели, времени суток
# # Диаграмма количества покупок по типу оплаты

df.to_csv(r"ecom_processed.csv")