import wbgapi as wb

# Countries to compare (ISO3 codes)
countries = ["DEU", "USA", "GBR", "FRA", "NLD", "ESP", "ITA", "IND", "CAN", "AUS"]

# SL.UEM.TOTL.ZS = Unemployment rate, % of labour force (ILO estimate)
df = wb.data.DataFrame(
    "SL.UEM.TOTL.ZS",
    countries,
    time=range(2015, 2026),
    labels=True
)

df.to_csv("data/raw/unemployment.csv")
print(df)
print("\nSaved to data/raw/unemployment.csv")