import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
INDEED = RAW / "indeed"
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def to_month(df):
    """Convert daily dates to the first day of each month."""
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


# ---------------------------------------------------------------
# 1. Country-level postings (all 9 countries)
# ---------------------------------------------------------------
frames = [pd.read_csv(f) for f in INDEED.glob("*_aggregate_job_postings_*.csv")]
agg = to_month(pd.concat(frames))
agg = agg[agg["variable"] == "total postings"]

fact_country = (agg.groupby(["month", "jobcountry"], as_index=False)
                   ["indeed_job_postings_index_SA"].mean()
                   .rename(columns={"jobcountry": "country_code",
                                    "indeed_job_postings_index_SA": "postings_index"}))
fact_country["postings_index"] = fact_country["postings_index"].round(2)
fact_country.to_csv(OUT / "fact_postings_country.csv", index=False)
print(f"fact_postings_country: {len(fact_country)} rows")


# ---------------------------------------------------------------
# 2. Sector-level postings (AU, CA, DE, FR, GB, US)
# ---------------------------------------------------------------
frames = [pd.read_csv(f) for f in INDEED.glob("*_job_postings_by_sector_*.csv")]
sec = to_month(pd.concat(frames))
sec = sec[sec["variable"] == "total postings"]

fact_sector = (sec.groupby(["month", "jobcountry", "display_name"], as_index=False)
                  ["indeed_job_postings_index"].mean()
                  .rename(columns={"jobcountry": "country_code",
                                   "display_name": "sector",
                                   "indeed_job_postings_index": "postings_index"}))
fact_sector["postings_index"] = fact_sector["postings_index"].round(2)
fact_sector.to_csv(OUT / "fact_postings_sector.csv", index=False)
print(f"fact_postings_sector: {len(fact_sector)} rows")


# ---------------------------------------------------------------
# 3. German regions (for the Germany deep-dive page)
# ---------------------------------------------------------------
STATES = {
    "bw": "Baden-Württemberg", "by": "Bayern", "be": "Berlin",
    "bb": "Brandenburg", "hb": "Bremen", "hh": "Hamburg",
    "he": "Hessen", "mv": "Mecklenburg-Vorpommern", "ni": "Niedersachsen",
    "nw": "Nordrhein-Westfalen", "rp": "Rheinland-Pfalz", "sl": "Saarland",
    "sn": "Sachsen", "st": "Sachsen-Anhalt", "sh": "Schleswig-Holstein",
    "th": "Thüringen",
}
reg = to_month(pd.read_csv(INDEED / "DE_regional_de.csv"))
fact_region = (reg.groupby(["month", "region"], as_index=False)
                  ["indeed_job_postings_index"].mean()
                  .rename(columns={"indeed_job_postings_index": "postings_index"}))
fact_region["state_name"] = fact_region["region"].map(STATES).fillna(fact_region["region"])
fact_region["postings_index"] = fact_region["postings_index"].round(2)
fact_region.to_csv(OUT / "fact_postings_de_region.csv", index=False)
print(f"fact_postings_de_region: {len(fact_region)} rows")


# ---------------------------------------------------------------
# 4. Unemployment (wide -> long)
# ---------------------------------------------------------------
unemp = pd.read_csv(RAW / "unemployment.csv")
fact_unemp = unemp.melt(id_vars=["economy", "Country"],
                        var_name="year", value_name="unemployment_rate")
fact_unemp["year"] = fact_unemp["year"].str.replace("YR", "").astype(int)
fact_unemp = (fact_unemp.dropna(subset=["unemployment_rate"])
                        .rename(columns={"economy": "country_code_iso3"})
                        .drop(columns="Country"))
fact_unemp["unemployment_rate"] = fact_unemp["unemployment_rate"].round(2)
fact_unemp.to_csv(OUT / "fact_unemployment.csv", index=False)
print(f"fact_unemployment: {len(fact_unemp)} rows")


# ---------------------------------------------------------------
# 5. Dimension: countries (joins Indeed ISO2 <-> World Bank ISO3)
# ---------------------------------------------------------------
dim_country = pd.DataFrame([
    ("DE", "DEU", "Germany",        "Europe"),
    ("FR", "FRA", "France",         "Europe"),
    ("GB", "GBR", "United Kingdom", "Europe"),
    ("NL", "NLD", "Netherlands",    "Europe"),
    ("ES", "ESP", "Spain",          "Europe"),
    ("IT", "ITA", "Italy",          "Europe"),
    ("US", "USA", "United States",  "North America"),
    ("CA", "CAN", "Canada",         "North America"),
    ("AU", "AUS", "Australia",      "Oceania"),
    ("IN", "IND", "India",          "Asia"),
], columns=["country_code", "country_code_iso3", "country_name", "region"])
dim_country.to_csv(OUT / "dim_country.csv", index=False)


# ---------------------------------------------------------------
# 6. Dimension: sectors, grouped for the "Tech / Data / Marketing" story
# ---------------------------------------------------------------
def sector_group(name):
    n = name.lower()
    if any(k in n for k in ["software", "it ", "it operations", "information design"]):
        return "Tech"
    if any(k in n for k in ["mathematics", "data", "scientific research"]):
        return "Data & Analytics"
    if any(k in n for k in ["marketing", "media", "communications", "advertising"]):
        return "Marketing"
    return "Other"

dim_sector = pd.DataFrame({"sector": sorted(fact_sector["sector"].unique())})
dim_sector["sector_group"] = dim_sector["sector"].apply(sector_group)
dim_sector.to_csv(OUT / "dim_sector.csv", index=False)

print("\nSector groups:")
print(dim_sector[dim_sector["sector_group"] != "Other"].to_string(index=False))
print(f"\nAll done! {len(dim_sector)} sectors. Files saved in data/processed/")