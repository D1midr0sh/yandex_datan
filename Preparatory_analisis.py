from math import isnan
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv('ecom_raw.csv', sep=',', decimal=".")

# PEP8
df.columns = [x.lower().replace(" ", "_") for x in df.columns]

# устранение пропусков по данным
colours = ['#FFCF48', '#F5617D']
sns.heatmap(df.isna(), cmap=sns.color_palette(colours), cbar=False)
plt.savefig("heatmap_of_missing_data.jpg", bbox_inches="tight")
print(f'Строки с пропусками составляют {round(df["channel"].isna().value_counts()[True] / len(df["channel"]) * 100, 2)}%')
print("Eсть пропуски в категориальных данных, пропущен регион, устройство и тип канала. "
      "\nТак как для ответа на основной вопрос исследования ключевыми являются регион и тип канала, "
      "то такие данные не могут помочь ответить на него. \nИх процентное соотношение маленькое и "
      "не было найдено рационального способа эти данные остановить, поэтому принято решение удалить эти строки.")
print("- - -")
df = df.dropna(how="any", subset=["channel", "region"])


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
df.loc[df["region"] == "Franсe", "region"] = "France"
df.loc[df["region"] == "Frаnce", "region"] = "France"
df.loc[df["region"] == "Frаncе", "region"] = "France"
df.loc[df["region"] == "UК", "region"] = "UK"

df["session_start"] = pd.to_datetime(df["session_start"])
df["session_end"] = pd.to_datetime(df["session_end"])
df["session_date"] = pd.to_datetime(df["session_date"])
df["order_dt"] = pd.to_datetime(df["order_dt"])
print(f'Исследуемый период с {max(df["session_start"]).date()} по {min(df["session_start"]).date()} продолжительностью'
      f' {(max(df["session_start"]) - min(df["session_start"])).days} дней')
# ТЗ (невыполненные пункты).
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