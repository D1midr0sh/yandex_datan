from math import isnan
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# функция для расчета тройного интерквартильного размаха
def inq(col):
    return df[col].quantile(.75) + (df[col].quantile(.75) - df[col].quantile(.25)) * 3

# функция для добавления нового столбца в зависимости от времени суток визита
def sort_by_time_of_day(time):
    time = time.hour
    if 10 > time >= 6:
        return "утро"
    if 17 > time >= 10:
        return "день"
    if 22 > time >= 17:
        return "вечер"
    if time >= 22 or time < 6:
        return "ночь"


df = pd.read_csv('ecom_raw.csv', sep=',', decimal=".")

# PEP8
df.columns = [x.lower().replace(" ", "_") for x in df.columns]

# устранение пропусков по данным
colours = ['#FFCF48', '#F5617D']
sns.heatmap(df.isna(), cmap=sns.color_palette(colours), cbar=False)
plt.savefig("graphics/heatmap_of_missing_data.jpg", bbox_inches="tight")
print(f'Строки с пропусками составляют {round(df["channel"].isna().value_counts()[True] / len(df["channel"]) * 100, 2)}%')
print("Eсть пропуски в категориальных данных, пропущен регион, устройство и тип канала. "
      "\nТак как для ответа на основной вопрос исследования ключевыми являются регион и тип канала, "
      "то такие данные не могут помочь ответить на него. \nИх процентное соотношение маленькое и "
      "не было найдено рационального способа эти данные остановить, поэтому принято решение удалить эти строки.")
print("- - -")
df = df.dropna(how="any", subset=["channel", "region"])


# столбец “payer” с информацией о том, является ли пользователь платящим или нет
df["payer"] = df["revenue"].apply(lambda x: int(not isnan(x)))

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

# преобразование данных с временными значениями
df["session_start"] = pd.to_datetime(df["session_start"])
df["session_end"] = pd.to_datetime(df["session_end"])
df["session_date"] = pd.to_datetime(df["session_date"])
df["order_dt"] = pd.to_datetime(df["order_dt"])


# проверка на ошибки в данных с временем
for index, row in df.iterrows():
    row_has_mistake = 0
    if row["session_start"] > row["session_end"] or row["sessiondurationsec"] < 0 :
        row_has_mistake = 1
    if row["session_date"].date() != row["session_start"].date():
        row_has_mistake = 1
    if row["month"] != row["session_date"].month or row["day"] != row["session_date"].day_of_week + 1:
        row_has_mistake = 1
    if row_has_mistake:
        print("Обнаружена ошибка в данных")


# период исследования
print(f'Исследуемый период с {max(df["session_date"]).date()} по {min(df["session_date"]).date()} продолжительностью'
      f' {(max(df["session_date"]) - min(df["session_date"])).days} дня')
sns.displot(df["session_date"], bins=12)
plt.savefig("graphics/session_date_spread.jpg")
plt.clf()
print("После построения гистограммы по месяцам видно, что количество записей распределены про месяцам ненормально, \nно при этом нет выбросов, поэтому стоит учитывать весть период.")
print("- - -")

# анализ на выбросы
sns.boxplot(df["sessiondurationsec"])
plt.savefig(f"graphics/boxplots_session_duration.jpg")
plt.clf()
sns.displot(df["day"], bins=7)
plt.savefig("graphics/boxplots_day_of_week.jpg")
plt.clf()
print("Ярко выраженной сезонности не обнаружено, но есть выбросы в большую сторону в длительности сессиии.")
print("Принято решение устранить их методом тройного интерквартильного размаха.")
print("Значения выбросов заменены медианой по группе канала рекламы.")
print("- - -")

# устранение выбросов
channels = list(set(df["channel"]))
for channel_type in channels:
    median = int(df.loc[df["channel"] == channel_type, "sessiondurationsec"].median())
    df.loc[(df["channel"] == channel_type) & (df["sessiondurationsec"] > inq("sessiondurationsec")), "sessiondurationsec"] = median

# столбец "time_of_day"
df["time_of_day"] = df["session_start"].apply(sort_by_time_of_day)

# ТЗ (невыполненные пункты).
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