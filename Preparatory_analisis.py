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

# Устранение пропусков по данным
colours = ['#FFCF48', '#F5617D']
sns.heatmap(df.isna(), cmap=sns.color_palette(colours), cbar=False)
plt.savefig("graphics/heatmap_of_missing_data.jpg", bbox_inches="tight")
print(f'Строки с пропусками составляют {round(df["channel"].isna().value_counts()[True] / len(df["channel"]) * 100, 2)}%')
print("Eсть пропуски в категориальных данных, пропущен регион, устройство и тип канала. "
      "\nПосле поиска по индексу в пропусках было обнаружено, что некоторые индексы совпадают с теми"
      "которые ранее были найдены в датасете. \nБыло принято решение подставить эти категориальные данные, а те строки"
      ", \nid которых ранее не встречался или в нем тоже отсутствуют категориальные данные, было принято решение удалить")
print("- - -")
df1 = pd.DataFrame(df[df["region"].isnull()]["user_id"])
values = pd.DataFrame(df["user_id"].value_counts())
for uid in df1["user_id"]:
    if values.loc[uid, "count"] == 2:
        line2 = df.loc[df["user_id"] == uid].iloc[0]
        df.loc[df["user_id"] == uid, "device"] = line2["device"]
        df.loc[df["user_id"] == uid, "region"] = line2["region"]
        df.loc[df["user_id"] == uid, "channel"] = line2["channel"]
df = df.dropna(how="any", subset=["channel", "region"])
df = df.reset_index(drop=True)


# Столбец “payer” с информацией о том, является ли пользователь платящим или нет
df["payer"] = df["revenue"].apply(lambda x: int(not isnan(x)))

# Округление длительности сессии (так как все числа очень близки к целому, вероятно ошибка в процессе передачи)
df["sessiondurationsec"] = df["sessiondurationsec"].apply(round)

# Устранение явных дубликатов
if len(df["user_id"]) != len(list(set(df["user_id"]))):
    df = df.drop_duplicates(ignore_index=True)

# Устранение ошибок в категориальных данных
df.loc[df["channel"] == "контексная реклама", "channel"] = "контекстная реклама"
df.loc[df["device"] == "android", "device"] = "Android"
df.loc[df["region"] == "Unjted States", "region"] = "United States"
df.loc[df["region"] == "germany", "region"] = "Germany"
df.loc[df["region"] == "Franсe", "region"] = "France"
df.loc[df["region"] == "Frаnce", "region"] = "France"
df.loc[df["region"] == "Frаncе", "region"] = "France"
df.loc[df["region"] == "UК", "region"] = "UK"

# Преобразование данных с временными значениями
df["session_start"] = pd.to_datetime(df["session_start"])
df["session_end"] = pd.to_datetime(df["session_end"])
df["session_date"] = pd.to_datetime(df["session_date"])
df["order_dt"] = pd.to_datetime(df["order_dt"])

# Проверка на ошибки в данных с временем
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

# Период исследования
print(f'Исследуемый период с {max(df["session_date"]).date()} по {min(df["session_date"]).date()} продолжительностью'
      f' {(max(df["session_date"]) - min(df["session_date"])).days} дня')
sns.displot(df["session_date"], bins=12)
plt.savefig("graphics/session_date_spread.jpg")
plt.clf()
print("После построения гистограммы по месяцам видно, что количество записей распределены про месяцам ненормально, \nно при этом нет выбросов, поэтому стоит учитывать весть период.")
print("- - -")

# Анализ на выбросы
sns.boxplot(df["sessiondurationsec"])
plt.savefig(f"graphics/boxplot_session_duration.jpg")
plt.clf()
sns.boxplot(df["revenue"])
plt.savefig(f"graphics/boxplot_revenue.jpg")
plt.clf()
sns.displot(df.loc[df["payer"] == 1, "revenue"])
plt.savefig(f"graphics/displot_revenue.jpg")
plt.clf()
print("Есть выбросы в большую сторону в длительности сессиии и доходе.")
print("Принято решение устранить их методом тройного интерквартильного размаха.")
print("Значения выбросов заменены медианой по группе канала рекламы и по региону.")

# Устранение выбросов
channels = list(set(df["channel"]))
regions = list(set(df["region"]))
sigma_revenue = round(df.loc[df["payer"] == 1, "revenue"].std())
mean_revenue = round(df.loc[df["payer"] == 1, "revenue"].mean())
for channel_type in channels:
    for region in regions:
        median_sessionduration = df.loc[(df["channel"] == channel_type) & (df["region"] == region), "sessiondurationsec"].median()
        if isnan(median_sessionduration):
            median_sessionduration = df.loc[(df["channel"] == channel_type), "sessiondurationsec"].median()
        df.loc[(df["channel"] == channel_type) & (df["region"] == region) &
               (df["sessiondurationsec"] > inq("sessiondurationsec")), "sessiondurationsec"] = int(median_sessionduration)

        # для дохода было принято решение использовать правило сигмы, так как интерквартильный размах отсекал данные, которые не показались команде выбросами
        median_revenue = df.loc[(df["channel"] == channel_type) & (df["region"] == region) & (df["payer"] == 1), "revenue"].median()
        if isnan(median_revenue):
            median_revenue = df.loc[(df["channel"] == channel_type) & (df["payer"] == 1), "revenue"].median()
        if median_revenue == 5499:
            median_revenue = 4999
        df.loc[(df["channel"] == channel_type) & (df["region"] == region) & (
                df["revenue"] > mean_revenue + sigma_revenue) & (df["payer"] == 1), "revenue"] = int(median_revenue)
        df.loc[(df["channel"] == channel_type) & (df["region"] == region) & (
                    df["revenue"] < abs(mean_revenue - sigma_revenue)) & (df["payer"] == 1), "revenue"] = int(median_revenue)

# Добавление столбца "time_of_day" в зависимости от времени суток
df["time_of_day"] = df["session_start"].apply(sort_by_time_of_day)

# Добавление столбца "promo_code" с итоговой суммой покупки после промокода 10%
df["final_price"] = df["revenue"]
df.loc[df["promo_code"] == 1, "final_price"] = df.loc[df["promo_code"] == 1, "final_price"].apply(lambda x: round(x * 0.9))

# Доля продаж по регионам
y = df.loc[df["payer"] == 1, "region"].value_counts()
plt.figure(figsize=(5, 5))
plt.pie(y, labels=y.index, labeldistance=1.05)
plt.suptitle("Доля продаж по регионам", size=16)
plt.savefig("graphics/sales_by_region.jpg")
plt.clf()

# Доля продаж по источникам
y = df.loc[df["payer"] == 1, "channel"].value_counts()
plt.figure(figsize=(7, 5))
plt.pie(y, labels=y.index, labeldistance=1.05)
plt.suptitle("Доля продаж по источникам", size=16)
plt.savefig("graphics/sales_by_channel.jpg")
plt.clf()

# Доля продаж по устройствам
y = df.loc[df["payer"] == 1, "device"].value_counts()
plt.figure(figsize=(5, 5))
plt.pie(y, labels=y.index, labeldistance=1.05)
plt.suptitle("Доля продаж по устройствам", size=16)
plt.savefig("graphics/sales_by_device.jpg")
plt.clf()

# Сезонность
sns.displot(df["day"], bins=7)
plt.suptitle("Сезонность по дням недели", size=16)
plt.savefig("graphics/displot_by_day_of_week.jpg")
plt.clf()
sns.displot(df["month"], bins=6)
plt.suptitle("Сезонность по месяцам", size=16)
plt.savefig("graphics/displot_by_month.jpg")
plt.clf()
sns.displot(df["time_of_day"], bins=4)
plt.suptitle("Сезонность по времени дня", size=16)
plt.savefig("graphics/displot_by_time_of_day.jpg")
plt.clf()

# Количество пользователей с разбивкой на платящих/не платящих по регионам
plt.figure(figsize=(5, 7))
sns.histplot(df, x="region", hue="payer", stat="count", multiple="stack")
plt.suptitle("Количество посетителей по регионам", size=16)
plt.savefig("graphics/visitors_and_region.jpg")
plt.clf()

# По устройствам
plt.figure(figsize=(5, 7))
sns.histplot(df, x="device", hue="payer", stat="count", multiple="stack")
plt.suptitle("Количество посетителей по устройствам", size=16)
plt.savefig("graphics/visitors_and_device.jpg")
plt.clf()

# По каналу рекламы
plt.figure(figsize=(5, 7))
sns.histplot(df, x="channel", hue="payer", stat="count", multiple="stack", cbar=False)
plt.suptitle("Количество посетителей \nпо каналу рекламы", size=16)
plt.xticks(rotation=19)
plt.savefig("graphics/visitors_and_channel.jpg")
plt.clf()

# Диаграмма количества покупок по типу оплаты
sns.histplot(df, x="payment_type", stat="count")
plt.xticks(rotation=18)
plt.suptitle("Количество покупок по типу оплаты", size=16)
plt.savefig("graphics/sales_and_payment_type.jpg")
plt.clf()

df.to_csv(r"ecom_processed.csv")