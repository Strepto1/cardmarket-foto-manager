import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import hashlib
import io
from datetime import datetime, timedelta, date

st.set_page_config(
    page_title="💰 Financieel Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
REKENING_NL47 = "NL47INGB0748806679"
REKENING_NL37 = "NL37INGB0666432228"

BETAAL_REKENINGEN = {
    REKENING_NL47: "Kevin persoonlijk",
    REKENING_NL37: "Gezamenlijk huishouden",
}

SPAAR_ZOONTJE     = "S 143-09136"
SPAAR_KEVIN       = "S 769-58442"
SPAAR_GEZAMENLIJK = "W 429-40824"
SPAAR_POKEMON     = "F 769-58441"

SPAAR_REKENINGEN = {
    SPAAR_ZOONTJE:     "Zoontje spaargeld",
    SPAAR_KEVIN:       "Kevin persoonlijk spaargeld",
    SPAAR_GEZAMENLIJK: "Gezamenlijk spaargeld (ING)",
    SPAAR_POKEMON:     "Pokémon business rekening",
}

ALL_REKENINGEN = {**BETAAL_REKENINGEN, **SPAAR_REKENINGEN}

HUISHOUDEN_BETAAL = [REKENING_NL37]
KEVIN_BETAAL      = [REKENING_NL47]
HUISHOUDEN_SPAAR  = [SPAAR_ZOONTJE, SPAAR_GEZAMENLIJK]
KEVIN_SPAAR       = [SPAAR_KEVIN, SPAAR_POKEMON]

COLOR_INCOME  = "#2ecc71"
COLOR_EXPENSE = "#e74c3c"
COLOR_NEUTRAL = "#3498db"
PLOTLY_TEMPLATE = "plotly_dark"

POKEMON_DIRECT_KW = [
    "pokemon", "cardmarket", "sammelkartenmarkt", "toretoku", "card rush",
    "yuyu", "hareruya", "torecolo", "buyandship", "tenso", "scolair",
]
POKEMON_PLATFORMS   = ["vinted", "marktplaats", "postnl", "tikkie"]
POKEMON_CONFIRM_KW  = [
    "pokemon", "poke", "kaart", "card", "booster", "etb", "pack",
    "tcg", "pikachu", "charizard",
]
POKEMON_SHIP_KW     = ["postnl"]
POKEMON_PLATFORM_KW = ["vinted", "marktplaats"]
POKEMON_DIRECT_SHOP = [
    "cardmarket", "sammelkartenmarkt", "toretoku", "yuyu",
    "hareruya", "torecolo", "buyandship", "tenso",
]

CATEGORY_KEYWORDS = [
    ("🛒 Supermarkt - Albert Heijn",  ["albert heijn", "ah to go"]),
    ("🛒 Supermarkt - Jumbo",         ["jumbo"]),
    ("🛒 Supermarkt - Lidl",          ["lidl"]),
    ("🛒 Supermarkt - Overig",        ["dirk", "aldi", "plus supermarkt", "hoogvliet"]),
    ("🍽️ Horeca & eten",             ["restaurant", "cafe", "coffeeshop", "mcdonalds",
                                       "subway", "dominos", "thuisbezorgd", "takeaway", "dutch chapter"]),
    ("⛽ Brandstof & auto",           ["shell", "bp", "esso", "total", "tinq", "q8",
                                       "parkeer", "parking"]),
    ("🏥 Zorg & gezondheid",          ["vink", "zorgverzekering", "apotheker", "apotheek",
                                       "tandarts", "huisarts"]),
    ("📱 Telecom & internet",         ["budget mobiel", "vodafone", "kpn", "odido",
                                       "t-mobile", "ziggo", "xs4all"]),
    ("🎬 Streaming & abonnementen",   ["viaplay", "netflix", "spotify", "disney",
                                       "videoland", "nent"]),
    ("🌍 Goede doelen & donaties",    ["planet wild", "greenpeace", "wwf", "amnesty",
                                       "kwf", "alpe d'huzes"]),
    ("🧒 Kinderopvang & kids",        ["kinderdagverblijf", "bso", "peuterspeelzaal"]),
    ("🐦 Fotografie & hobby",         ["camera", "vogelbescherming", "sigma", "dikkebirdpics"]),
    ("🏠 Wonen & utilities",          ["huur", "hypotheek", "energie", "vattenfall",
                                       "nuon", "eneco", "ennatuurlijk", "gemeente"]),
    ("📦 Verzendkosten overig",       ["postnl", "dhl", "dpd", "ups"]),
    ("🏷️ Overig verkoop",            ["vinted", "marktplaats"]),
    ("💸 Interne overboekingen",      [
        REKENING_NL47.lower(), REKENING_NL37.lower(),
        "spaarrekening", "overboeking",
    ]),
]

ALL_CATEGORIES = (
    ["🃏 Pokémon business"]
    + [c for c, _ in CATEGORY_KEYWORDS]
    + ["❓ Overig"]
)


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def fmt_eur(amount) -> str:
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "€ 0,00"
    sign = "-" if amount < 0 else ""
    s = f"{abs(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}€\u00a0{s}"


def parse_amount(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).strip().replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def make_tx_id(datum, rekening, bedrag_raw, naam) -> str:
    key = f"{datum}_{rekening}_{bedrag_raw}_{str(naam)[:60]}"
    return hashlib.md5(key.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────
# CATEGORISATION
# ─────────────────────────────────────────────────────────────────

def pokemon_subcategory(naam_low: str, med_low: str) -> str:
    combined = naam_low + " " + med_low
    for kw in POKEMON_SHIP_KW:
        if kw in combined:
            return "Verzending"
    for kw in POKEMON_PLATFORM_KW:
        if kw in combined:
            return "Verkoop platforms"
    for kw in POKEMON_DIRECT_SHOP:
        if kw in combined:
            return "Directe inkoop"
    return "Overig pokémon"


def categorize(naam, mededelingen, rekening, tegenrekening="",
               corrections: dict = None, tx_id: str = None):
    """Return (category, pokemon_subcat_or_None)."""
    if corrections and tx_id and tx_id in corrections:
        return corrections[tx_id], None

    nl = str(naam).lower()        if pd.notna(naam)        else ""
    ml = str(mededelingen).lower() if pd.notna(mededelingen) else ""
    tl = str(tegenrekening).lower() if pd.notna(tegenrekening) else ""
    combined = nl + " " + ml + " " + tl

    # Pokémon savings account
    if rekening == SPAAR_POKEMON:
        return "🃏 Pokémon business", pokemon_subcategory(nl, ml)

    # Direct Pokémon keywords
    for kw in POKEMON_DIRECT_KW:
        if kw in combined:
            return "🃏 Pokémon business", pokemon_subcategory(nl, ml)

    # Conditional: platform + pokémon keyword in mededelingen
    is_platform   = any(p in nl for p in POKEMON_PLATFORMS)
    has_pokemon_kw = any(kw in ml for kw in POKEMON_CONFIRM_KW)
    if is_platform and has_pokemon_kw:
        return "🃏 Pokémon business", pokemon_subcategory(nl, ml)

    # Other categories
    for cat, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in nl or kw in ml:
                return cat, None

    return "❓ Overig", None


# ─────────────────────────────────────────────────────────────────
# CSV PARSING
# ─────────────────────────────────────────────────────────────────

def _read_csv(content: bytes) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return pd.read_csv(io.BytesIO(content), sep=";", dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(content), sep=";", dtype=str, encoding="latin-1")


def parse_betaal_csv(content: bytes) -> pd.DataFrame:
    df = _read_csv(content)
    df.columns = [c.strip() for c in df.columns]

    df["Datum"] = pd.to_datetime(
        df["Datum"].astype(str).str.strip(), format="%Y%m%d", errors="coerce"
    )

    bedrag_col = "Bedrag (EUR)" if "Bedrag (EUR)" in df.columns else "Bedrag"
    df["Bedrag_raw"] = df[bedrag_col].astype(str).str.strip()
    df["Bedrag"]     = df["Bedrag_raw"].apply(parse_amount)
    df["Saldo"]      = df["Saldo na mutatie"].apply(parse_amount)

    df["Af Bij"] = df["Af Bij"].str.strip()
    df["Bedrag_signed"] = df.apply(
        lambda r: r["Bedrag"] if r["Af Bij"] == "Bij" else -r["Bedrag"], axis=1
    )

    for col in ["Naam / Omschrijving", "Mededelingen", "Tegenrekening", "Tag", "Mutatiesoort"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("")

    df["bron"]  = "betaal"
    df["tx_id"] = df.apply(
        lambda r: make_tx_id(r["Datum"], r["Rekening"], r["Bedrag_raw"], r["Naam / Omschrijving"]),
        axis=1,
    )
    return df


def parse_spaar_csv(content: bytes) -> pd.DataFrame:
    df = _read_csv(content)
    df.columns = [c.strip() for c in df.columns]

    df["Datum"] = pd.to_datetime(
        df["Datum"].astype(str).str.strip(), format="%Y-%m-%d", errors="coerce"
    )

    df["Naam / Omschrijving"] = df.get("Omschrijving", pd.Series([""] * len(df), dtype=str))
    df["Bedrag_raw"] = df["Bedrag"].astype(str).str.strip()
    df["Bedrag"]     = df["Bedrag_raw"].apply(parse_amount)
    df["Saldo"]      = df["Saldo na mutatie"].apply(parse_amount)

    df["Af Bij"] = df["Af Bij"].str.strip()
    df["Bedrag_signed"] = df.apply(
        lambda r: r["Bedrag"] if r["Af Bij"] == "Bij" else -r["Bedrag"], axis=1
    )

    for col in ["Mededelingen", "Tegenrekening", "Rekening naam", "Mutatiesoort"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("")

    df["bron"]  = "spaar"
    df["tx_id"] = df.apply(
        lambda r: make_tx_id(r["Datum"], r["Rekening"], r["Bedrag_raw"], r["Naam / Omschrijving"]),
        axis=1,
    )
    return df


def merge_incremental(existing, new_df):
    """Returns (merged, n_added, n_dupes)."""
    if existing is None or len(existing) == 0:
        return new_df.copy(), len(new_df), 0
    existing_ids = set(existing["tx_id"].values)
    is_new  = ~new_df["tx_id"].isin(existing_ids)
    n_added = int(is_new.sum())
    n_dupes = len(new_df) - n_added
    merged  = pd.concat([existing, new_df[is_new]], ignore_index=True)
    merged  = merged.sort_values("Datum").reset_index(drop=True)
    return merged, n_added, n_dupes


# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "betaal_df":         None,
        "spaar_df":          None,
        "corrections":       {},
        "betaal_file_hash":  None,
        "spaar_file_hash":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────
# DATA ACCESS
# ─────────────────────────────────────────────────────────────────

def apply_cats(df: pd.DataFrame) -> pd.DataFrame:
    corrections = st.session_state.corrections
    results = df.apply(
        lambda r: categorize(
            r.get("Naam / Omschrijving", ""),
            r.get("Mededelingen", ""),
            r.get("Rekening", ""),
            r.get("Tegenrekening", ""),
            corrections=corrections,
            tx_id=r.get("tx_id", ""),
        ),
        axis=1, result_type="expand",
    )
    df = df.copy()
    df["Categorie"]     = results[0]
    df["Pokemon_subcat"] = results[1]
    return df


def get_betaal(date_from, date_to, account_filter) -> pd.DataFrame:
    df = st.session_state.betaal_df
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df = apply_cats(df)
    df = df[(df["Datum"].dt.date >= date_from) & (df["Datum"].dt.date <= date_to)]
    if "NL47" in account_filter:
        df = df[df["Rekening"] == REKENING_NL47]
    elif "NL37" in account_filter:
        df = df[df["Rekening"] == REKENING_NL37]
    return df.copy()


def get_spaar(date_from, date_to) -> pd.DataFrame:
    df = st.session_state.spaar_df
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df = df[(df["Datum"].dt.date >= date_from) & (df["Datum"].dt.date <= date_to)]
    return df.copy()


def no_data():
    st.info("📂 Upload je CSV-bestanden via de sidebar om te beginnen.")


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.title("💰 Financieel Dashboard")
        st.divider()

        page = st.radio(
            "Navigatie",
            ["📊 Overzicht", "🛒 Uitgavencategorieën", "💰 Spaaranalyse",
             "🃏 Pokémon P&L", "🔍 Abonnementen", "📅 Maandvergelijking"],
            label_visibility="collapsed",
        )

        st.divider()
        st.subheader("📂 Data uploaden")

        betaal_file = st.file_uploader("Betaalrekeningen CSV", type=["csv"], key="bu")
        spaar_file  = st.file_uploader("Spaarrekeningen CSV",  type=["csv"], key="su")

        if betaal_file is not None:
            raw = betaal_file.read()
            fh  = hashlib.md5(raw).hexdigest()
            if fh != st.session_state.betaal_file_hash:
                new_df = parse_betaal_csv(raw)
                merged, n_added, n_dupes = merge_incremental(st.session_state.betaal_df, new_df)
                st.session_state.betaal_df        = merged
                st.session_state.betaal_file_hash = fh
                st.success(f"✅ {n_added} nieuwe transacties toegevoegd, {n_dupes} duplicaten overgeslagen.")

        if spaar_file is not None:
            raw = spaar_file.read()
            fh  = hashlib.md5(raw).hexdigest()
            if fh != st.session_state.spaar_file_hash:
                new_df = parse_spaar_csv(raw)
                merged, n_added, n_dupes = merge_incremental(st.session_state.spaar_df, new_df)
                st.session_state.spaar_df        = merged
                st.session_state.spaar_file_hash = fh
                st.success(f"✅ {n_added} nieuwe transacties toegevoegd, {n_dupes} duplicaten overgeslagen.")

        if st.session_state.betaal_df is not None:
            csv_out = st.session_state.betaal_df.drop(
                columns=["tx_id"], errors="ignore"
            ).to_csv(index=False, sep=";", decimal=",")
            st.download_button(
                "💾 Export betaaldata CSV", data=csv_out,
                file_name=f"betaal_master_{date.today()}.csv", mime="text/csv",
            )

        st.divider()
        st.subheader("🔧 Filters")

        bdf = st.session_state.betaal_df
        if bdf is not None and len(bdf) > 0:
            min_d = bdf["Datum"].min().date()
            max_d = bdf["Datum"].max().date()
        else:
            min_d = date(2023, 1, 1)
            max_d = date.today()

        date_from = st.date_input("Van", value=min_d, min_value=min_d, max_value=max_d)
        date_to   = st.date_input("Tot", value=max_d, min_value=min_d, max_value=max_d)

        account_filter = st.selectbox(
            "Rekening",
            ["Beide", "NL47 – Kevin persoonlijk", "NL37 – Gezamenlijk"],
        )

    return page, date_from, date_to, account_filter


# ─────────────────────────────────────────────────────────────────
# PAGE 1 – OVERZICHT
# ─────────────────────────────────────────────────────────────────

def page_overzicht(date_from, date_to, account_filter):
    st.title("📊 Overzicht")

    betaal = get_betaal(date_from, date_to, account_filter)
    spaar  = get_spaar(date_from, date_to)

    if len(betaal) == 0 and len(spaar) == 0:
        no_data(); return

    # ── Netto vermogen ──────────────────────────────────────────
    st.subheader("💎 Netto Vermogen")

    bdf_full = st.session_state.betaal_df
    sdf_full = st.session_state.spaar_df

    hh_betaal = kevin_betaal = hh_spaar = kevin_spaar = 0.0

    if bdf_full is not None and len(bdf_full) > 0:
        last_b = bdf_full.sort_values("Datum").groupby("Rekening")["Saldo"].last()
        hh_betaal    = sum(last_b.get(r, 0) for r in HUISHOUDEN_BETAAL)
        kevin_betaal = sum(last_b.get(r, 0) for r in KEVIN_BETAAL)

    if sdf_full is not None and len(sdf_full) > 0:
        last_s = sdf_full.sort_values("Datum").groupby("Rekening")["Saldo"].last()
        hh_spaar    = sum(last_s.get(r, 0) for r in HUISHOUDEN_SPAAR if r in last_s.index)
        kevin_spaar = sum(last_s.get(r, 0) for r in KEVIN_SPAAR     if r in last_s.index)

    hh_tot    = hh_betaal + hh_spaar
    kevin_tot = kevin_betaal + kevin_spaar
    totaal    = hh_tot + kevin_tot

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🏠 Huishouden totaal", fmt_eur(hh_tot))
        st.caption(f"Betaal: {fmt_eur(hh_betaal)} · Spaar: {fmt_eur(hh_spaar)}")
    with c2:
        st.metric("👤 Kevin persoonlijk", fmt_eur(kevin_tot))
        st.caption(f"Betaal: {fmt_eur(kevin_betaal)} · Spaar: {fmt_eur(kevin_spaar)}")
    with c3:
        st.metric("💰 Totaal netto vermogen", fmt_eur(totaal))

    st.divider()

    # ── Maandelijks cashflow ────────────────────────────────────
    if len(betaal) > 0:
        st.subheader("📈 Maandelijks Kasstroomoverzicht")
        betaal = betaal.copy()
        betaal["Maand"] = betaal["Datum"].dt.to_period("M").astype(str)
        betaal["Rek_label"] = betaal["Rekening"].map(BETAAL_REKENINGEN).fillna(betaal["Rekening"])

        fig = go.Figure()
        for rek_label in betaal["Rek_label"].unique():
            sub = betaal[betaal["Rek_label"] == rek_label]
            bij = sub[sub["Af Bij"] == "Bij"].groupby("Maand")["Bedrag"].sum()
            af  = sub[sub["Af Bij"] == "Af"].groupby("Maand")["Bedrag"].sum()
            maanden = sorted(set(bij.index) | set(af.index))
            bij = bij.reindex(maanden, fill_value=0)
            af  = af.reindex(maanden,  fill_value=0)
            netto = bij - af

            fig.add_trace(go.Bar(
                name=f"Inkomsten ({rek_label})", x=maanden, y=bij.values,
                marker_color=COLOR_INCOME, opacity=0.8,
            ))
            fig.add_trace(go.Bar(
                name=f"Uitgaven ({rek_label})", x=maanden, y=-af.values,
                marker_color=COLOR_EXPENSE, opacity=0.8,
            ))
            fig.add_trace(go.Scatter(
                name=f"Netto ({rek_label})", x=maanden, y=netto.values,
                mode="lines+markers", line=dict(width=2),
            ))

        fig.update_layout(
            template=PLOTLY_TEMPLATE, barmode="relative", height=450,
            xaxis_title="Maand", yaxis_title="Bedrag (€)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Spaarverloop ────────────────────────────────────────────
    if len(spaar) > 0:
        st.subheader("💹 Spaarverloop per Rekening")
        spaar = spaar.copy()
        spaar["Rek_label"] = spaar["Rekening"].map(SPAAR_REKENINGEN).fillna(spaar["Rekening"])
        colors = px.colors.qualitative.Plotly
        fig2 = go.Figure()
        for i, (rek, label) in enumerate(SPAAR_REKENINGEN.items()):
            sub = spaar[spaar["Rekening"] == rek].sort_values("Datum")
            if len(sub) == 0:
                continue
            fig2.add_trace(go.Scatter(
                x=sub["Datum"], y=sub["Saldo"], name=label,
                mode="lines", line=dict(shape="spline", color=colors[i % len(colors)]),
                hovertemplate=f"<b>{label}</b><br>%{{x|%d-%m-%Y}}<br>Saldo: €%{{y:,.2f}}<extra></extra>",
            ))
        fig2.update_layout(
            template=PLOTLY_TEMPLATE, height=400,
            xaxis_title="Datum", yaxis_title="Saldo (€)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Recente grote transacties ───────────────────────────────
    if len(betaal) > 0:
        st.subheader("🔍 Grootste Uitgaven (afgelopen 30 dagen)")
        cutoff = pd.Timestamp(date_to) - pd.Timedelta(days=30)
        recent = betaal[(betaal["Datum"] >= cutoff) & (betaal["Af Bij"] == "Af")]
        top10  = recent.nlargest(10, "Bedrag").copy()
        top10["Datum"]   = top10["Datum"].dt.strftime("%d-%m-%Y")
        top10["Bedrag"]  = top10["Bedrag"].apply(fmt_eur)
        top10["Rekening"] = top10["Rekening"].map(BETAAL_REKENINGEN).fillna(top10["Rekening"])
        st.dataframe(
            top10[["Datum", "Naam / Omschrijving", "Rekening", "Bedrag", "Categorie"]]
            .rename(columns={"Naam / Omschrijving": "Omschrijving"}),
            use_container_width=True, hide_index=True,
        )


# ─────────────────────────────────────────────────────────────────
# PAGE 2 – UITGAVENCATEGORIEËN
# ─────────────────────────────────────────────────────────────────

def page_categorieen(date_from, date_to, account_filter):
    st.title("🛒 Uitgavencategorieën")

    betaal = get_betaal(date_from, date_to, account_filter)
    if len(betaal) == 0:
        no_data(); return

    uitgaven = betaal[betaal["Af Bij"] == "Af"].copy()

    tab1, tab2, tab3, tab4 = st.tabs(["🍩 Donut", "📈 Trends", "🛒 Supermarkt", "✏️ Correcties"])

    # ── Tab 1: Donut ────────────────────────────────────────────
    with tab1:
        cat_sum = (
            uitgaven.groupby("Categorie")["Bedrag"].sum()
            .sort_values(ascending=False).reset_index()
        )
        fig = px.pie(
            cat_sum, values="Bedrag", names="Categorie", hole=0.45,
            title="Totale uitgaven per categorie", template=PLOTLY_TEMPLATE,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        cat_sum["Bedrag"] = cat_sum["Bedrag"].apply(fmt_eur)
        st.dataframe(cat_sum.rename(columns={"Bedrag": "Totaal"}),
                     use_container_width=True, hide_index=True)

    # ── Tab 2: Trends ───────────────────────────────────────────
    with tab2:
        avail = sorted(uitgaven["Categorie"].unique())
        sel   = st.multiselect("Categorieën", avail, default=avail[:5])
        if sel:
            td = (
                uitgaven[uitgaven["Categorie"].isin(sel)]
                .assign(Maand=lambda d: d["Datum"].dt.to_period("M").astype(str))
                .groupby(["Maand", "Categorie"])["Bedrag"].sum().reset_index()
            )
            fig2 = px.line(
                td, x="Maand", y="Bedrag", color="Categorie",
                markers=True, template=PLOTLY_TEMPLATE,
                title="Maandelijkse uitgaven per categorie",
                labels={"Maand": "Maand", "Bedrag": "Bedrag (€)"},
            )
            fig2.update_layout(height=450)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Supermarkt ───────────────────────────────────────
    with tab3:
        sm_cats = [c for c in uitgaven["Categorie"].unique() if "Supermarkt" in c]
        sm = (
            uitgaven[uitgaven["Categorie"].isin(sm_cats)]
            .assign(Maand=lambda d: d["Datum"].dt.to_period("M").astype(str))
            .groupby(["Maand", "Categorie"])["Bedrag"].sum().reset_index()
        )
        if len(sm) > 0:
            fig3 = px.bar(
                sm, x="Maand", y="Bedrag", color="Categorie", barmode="stack",
                title="Supermarkt uitgaven per keten per maand", template=PLOTLY_TEMPLATE,
                labels={"Maand": "Maand", "Bedrag": "Bedrag (€)"},
            )
            fig3.update_layout(height=400)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Geen supermarkt-transacties gevonden.")

    # ── Tab 4: Correcties ───────────────────────────────────────
    with tab4:
        st.caption("Selecteer een transactie en pas de categorie handmatig aan. Correcties overleven de sessie.")

        show = betaal[["tx_id", "Datum", "Naam / Omschrijving", "Bedrag",
                        "Af Bij", "Categorie", "Mededelingen"]].copy()
        show["Datum"] = show["Datum"].dt.strftime("%d-%m-%Y")
        show["Bedrag_fmt"] = show.apply(
            lambda r: fmt_eur(r["Bedrag"] if r["Af Bij"] == "Bij" else -r["Bedrag"]), axis=1
        )

        search = st.text_input("🔍 Zoek op omschrijving", "")
        if search:
            show = show[show["Naam / Omschrijving"].str.contains(search, case=False, na=False)]

        if len(show) > 0:
            idx = st.selectbox(
                "Transactie",
                range(len(show)),
                format_func=lambda i: (
                    f"{show.iloc[i]['Datum']} — "
                    f"{str(show.iloc[i]['Naam / Omschrijving'])[:45]} — "
                    f"{show.iloc[i]['Bedrag_fmt']}"
                ),
            )
            row = show.iloc[idx]
            cur = row["Categorie"]
            c1, c2 = st.columns([3, 1])
            with c1:
                new_cat = st.selectbox(
                    "Nieuwe categorie", ALL_CATEGORIES,
                    index=ALL_CATEGORIES.index(cur) if cur in ALL_CATEGORIES else 0,
                )
            with c2:
                st.write("")
                st.write("")
                if st.button("✅ Toepassen"):
                    st.session_state.corrections[row["tx_id"]] = new_cat
                    st.success(f"Aangepast naar '{new_cat}'")
                    st.rerun()

        # Active corrections
        if st.session_state.corrections:
            st.subheader(f"Actieve correcties ({len(st.session_state.corrections)})")
            cdf = pd.DataFrame(
                [{"Categorie": v} for v in st.session_state.corrections.values()]
            )
            st.dataframe(cdf, use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.session_state.corrections:
                jdata = json.dumps(st.session_state.corrections, indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 Export correcties (JSON)", jdata,
                    file_name=f"correcties_{date.today()}.json", mime="application/json",
                )
        with col_b:
            cu = st.file_uploader("📤 Importeer correcties (JSON)", type=["json"], key="cu")
            if cu:
                loaded = json.loads(cu.read())
                st.session_state.corrections.update(loaded)
                st.success(f"{len(loaded)} correcties geladen.")


# ─────────────────────────────────────────────────────────────────
# PAGE 3 – SPAARANALYSE
# ─────────────────────────────────────────────────────────────────

def page_spaaranalyse(date_from, date_to, account_filter):
    st.title("💰 Spaaranalyse")

    spaar = get_spaar(date_from, date_to)
    if len(spaar) == 0:
        no_data(); return

    spaar = spaar.copy()
    spaar["Rek_label"] = spaar["Rekening"].map(SPAAR_REKENINGEN).fillna(spaar["Rekening"])

    # ── Tijdlijn ────────────────────────────────────────────────
    st.subheader("📈 Spaarsaldo Tijdlijn")
    colors = px.colors.qualitative.Plotly
    fig = go.Figure()
    for i, (rek, label) in enumerate(SPAAR_REKENINGEN.items()):
        sub = spaar[spaar["Rekening"] == rek].sort_values("Datum")
        if len(sub) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=sub["Datum"], y=sub["Saldo"], name=label,
            mode="lines", line=dict(shape="spline", color=colors[i % len(colors)]),
            hovertemplate=(
                f"<b>{label}</b><br>%{{x|%d-%m-%Y}}<br>"
                "Saldo: €%{y:,.2f}<br>%{customdata}<extra></extra>"
            ),
            customdata=sub["Naam / Omschrijving"].values,
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE, height=420,
        xaxis_title="Datum", yaxis_title="Saldo (€)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Maandelijkse inleg/opname ────────────────────────────────
    st.subheader("📋 Maandelijkse Inleg & Opname")
    spaar["Maand"] = spaar["Datum"].dt.to_period("M").astype(str)
    monthly = (
        spaar.groupby(["Maand", "Rek_label", "Af Bij"])["Bedrag"]
        .sum().reset_index()
        .pivot_table(index=["Maand", "Rek_label"], columns="Af Bij",
                     values="Bedrag", aggfunc="sum")
        .fillna(0).reset_index()
    )
    for col in ("Bij", "Af"):
        if col not in monthly.columns:
            monthly[col] = 0.0
    monthly["Netto"] = monthly["Bij"] - monthly["Af"]
    disp = monthly.copy()
    disp["Bij"]   = disp["Bij"].apply(fmt_eur)
    disp["Af"]    = disp["Af"].apply(fmt_eur)
    disp["Netto"] = disp["Netto"].apply(fmt_eur)
    disp.columns  = [c if c not in ("Bij","Af","Netto") else
                     {"Bij":"Inleg","Af":"Opname","Netto":"Netto"}[c] for c in disp.columns]
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.divider()

    # ── Spaardoelstelling ───────────────────────────────────────
    st.subheader("🎯 Spaardoelstelling")
    c1, c2 = st.columns(2)
    with c1:
        goal = st.number_input("Spaardoel (€)", min_value=0, value=20000, step=500)
        target = st.selectbox(
            "Voor rekening",
            list(SPAAR_REKENINGEN.values()) + ["Alle rekeningen"],
            index=len(SPAAR_REKENINGEN),
        )

    rev_map = {v: k for k, v in SPAAR_REKENINGEN.items()}
    if target == "Alle rekeningen":
        cur_saldo = spaar.sort_values("Datum").groupby("Rekening")["Saldo"].last().sum()
        acc_data  = spaar
    else:
        rek_key  = rev_map.get(target)
        sub_data = spaar[spaar["Rekening"] == rek_key] if rek_key else pd.DataFrame()
        cur_saldo = sub_data.sort_values("Datum")["Saldo"].iloc[-1] if len(sub_data) > 0 else 0.0
        acc_data  = sub_data

    progress = min(cur_saldo / goal, 1.0) if goal > 0 else 0.0
    with c2:
        st.metric("Huidig saldo",  fmt_eur(cur_saldo))
        st.metric("Doelstelling",  fmt_eur(goal))
        st.metric("Resterend",     fmt_eur(max(goal - cur_saldo, 0)))
        st.progress(progress, text=f"{progress*100:.1f}% van doel bereikt")

    bij_data = acc_data[acc_data["Af Bij"] == "Bij"] if len(acc_data) > 0 else pd.DataFrame()
    if len(bij_data) > 0:
        avg_maand = bij_data.copy()
        avg_maand["Maand"] = avg_maand["Datum"].dt.to_period("M")
        avg_m = avg_maand.groupby("Maand")["Bedrag"].sum().mean()
        if avg_m > 0 and cur_saldo < goal:
            mnd = (goal - cur_saldo) / avg_m
            projected = datetime.now() + timedelta(days=mnd * 30.4)
            st.info(
                f"📅 Bij gemiddelde inleg van {fmt_eur(avg_m)}/maand bereik je je doel "
                f"rond **{projected.strftime('%B %Y')}**."
            )

    st.divider()

    # ── Rendement ───────────────────────────────────────────────
    st.subheader("📊 Rendementsanalyse")
    sdf_full = st.session_state.spaar_df
    if sdf_full is not None and len(sdf_full) > 0:
        for rek, label in SPAAR_REKENINGEN.items():
            sub = sdf_full[sdf_full["Rekening"] == rek].sort_values("Datum").copy()
            if len(sub) < 4:
                continue
            sub["Maand"] = sub["Datum"].dt.to_period("M")
            inleg = sub[sub["Af Bij"] == "Bij"].groupby("Maand")["Bedrag"].sum()
            saldo_change = sub.groupby("Maand")["Saldo"].last().diff()
            comp = pd.DataFrame({"inleg": inleg, "groei": saldo_change}).dropna()
            if len(comp) == 0:
                continue
            rente = (comp["groei"] - comp["inleg"]).mean()
            if rente > 0.5:
                st.success(f"📈 **{label}**: Gemiddeld {fmt_eur(rente)}/maand extra groei door rente")
            else:
                st.warning(f"📉 **{label}**: Saldo groeit niet sneller dan inleg")


# ─────────────────────────────────────────────────────────────────
# PAGE 4 – POKÉMON P&L
# ─────────────────────────────────────────────────────────────────

def page_pokemon(date_from, date_to, account_filter):
    st.title("🃏 Pokémon P&L")

    betaal = get_betaal(date_from, date_to, account_filter)
    spaar  = get_spaar(date_from, date_to)

    if len(betaal) == 0 and len(spaar) == 0:
        no_data(); return

    # Collect pokémon transactions
    frames = []
    if len(betaal) > 0:
        pk_betaal = betaal[betaal["Categorie"] == "🃏 Pokémon business"].copy()
        if len(pk_betaal) > 0:
            frames.append(pk_betaal)

    if len(spaar) > 0:
        pk_spaar = spaar[spaar["Rekening"] == SPAAR_POKEMON].copy()
        if len(pk_spaar) > 0:
            pk_spaar["Categorie"]      = "🃏 Pokémon business"
            pk_spaar["Pokemon_subcat"] = pk_spaar.apply(
                lambda r: pokemon_subcategory(
                    str(r.get("Naam / Omschrijving","")).lower(),
                    str(r.get("Mededelingen","")).lower(),
                ), axis=1,
            )
            frames.append(pk_spaar)

    if not frames:
        st.info("Geen pokémon-transacties gevonden."); return

    poke = pd.concat(frames, ignore_index=True).sort_values("Datum")
    poke["Rek_label"] = poke["Rekening"].map(ALL_REKENINGEN).fillna(poke["Rekening"])
    if "Pokemon_subcat" not in poke.columns:
        poke["Pokemon_subcat"] = "Overig pokémon"

    # ── Overzicht metrics ───────────────────────────────────────
    st.subheader("💡 Totaaloverzicht")
    inkomsten = poke[poke["Af Bij"] == "Bij"]["Bedrag"].sum()
    uitgaven  = poke[poke["Af Bij"] == "Af"]["Bedrag"].sum()
    netto     = inkomsten - uitgaven
    roi       = (netto / uitgaven * 100) if uitgaven > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 Totale inkomsten", fmt_eur(inkomsten))
    c2.metric("📉 Totale kosten",    fmt_eur(uitgaven))
    c3.metric("💰 Netto resultaat",  fmt_eur(netto))
    c4.metric("📊 ROI",              f"{roi:+.1f}%")

    st.divider()

    # ── Maandelijkse P&L ────────────────────────────────────────
    st.subheader("📊 Maandelijkse P&L")
    poke["Maand"] = poke["Datum"].dt.to_period("M").astype(str)
    mp = (
        poke.groupby(["Maand","Af Bij"])["Bedrag"].sum()
        .reset_index()
        .pivot_table(index="Maand", columns="Af Bij", values="Bedrag", aggfunc="sum")
        .fillna(0).reset_index().sort_values("Maand")
    )
    for col in ("Bij","Af"):
        if col not in mp.columns: mp[col] = 0.0
    mp["Netto"]      = mp["Bij"] - mp["Af"]
    mp["Cumulatief"] = mp["Netto"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Inkomsten", x=mp["Maand"], y=mp["Bij"],   marker_color=COLOR_INCOME))
    fig.add_trace(go.Bar(name="Kosten",    x=mp["Maand"], y=-mp["Af"],   marker_color=COLOR_EXPENSE))
    fig.add_trace(go.Scatter(
        name="Cumulatief", x=mp["Maand"], y=mp["Cumulatief"],
        mode="lines+markers", line=dict(color=COLOR_NEUTRAL, width=2), yaxis="y2",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE, barmode="relative", height=450,
        xaxis_title="Maand",
        yaxis=dict(title="Bedrag (€)"),
        yaxis2=dict(title="Cumulatief (€)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Subcategorieën ──────────────────────────────────────────
    st.subheader("📂 Subcategorieën")
    sc = poke.groupby(["Pokemon_subcat","Af Bij"])["Bedrag"].sum().reset_index()
    fig2 = px.bar(
        sc, x="Pokemon_subcat", y="Bedrag", color="Af Bij", barmode="group",
        color_discrete_map={"Bij": COLOR_INCOME, "Af": COLOR_EXPENSE},
        title="Bedragen per subcategorie", template=PLOTLY_TEMPLATE,
        labels={"Pokemon_subcat": "Subcategorie", "Bedrag": "Bedrag (€)", "Af Bij": "Richting"},
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Transactietabel ─────────────────────────────────────────
    st.subheader("📋 Pokémon Transacties")
    disp = poke[["Datum","Naam / Omschrijving","Rek_label","Bedrag","Af Bij","Pokemon_subcat"]].copy()
    disp["Datum"]  = disp["Datum"].dt.strftime("%d-%m-%Y")
    disp["Bedrag"] = disp.apply(
        lambda r: fmt_eur(r["Bedrag"] if r["Af Bij"]=="Bij" else -r["Bedrag"]), axis=1
    )
    disp = disp.rename(columns={
        "Naam / Omschrijving": "Omschrijving",
        "Rek_label":           "Rekening",
        "Af Bij":              "Richting",
        "Pokemon_subcat":      "Subcategorie",
    })
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.divider()

    # ── Keyword review ──────────────────────────────────────────
    st.subheader("🔎 Keyword Review — mogelijk gemiste pokémon transacties")
    st.caption("Tikkie, Vinted, Marktplaats, PostNL niet als Pokémon maar bedrag > €15")

    if len(betaal) > 0:
        review_kw = ["tikkie", "vinted", "marktplaats", "postnl"]
        mask = (
            (betaal["Categorie"] != "🃏 Pokémon business") &
            (betaal["Naam / Omschrijving"].str.lower().str.contains(
                "|".join(review_kw), na=False)) &
            (betaal["Bedrag"] > 15)
        )
        review = betaal[mask].copy()

        if len(review) > 0:
            review["Datum"]     = review["Datum"].dt.strftime("%d-%m-%Y")
            review["Bedrag_fmt"] = review["Bedrag"].apply(fmt_eur)
            st.dataframe(
                review[["Datum","Naam / Omschrijving","Bedrag_fmt","Categorie","Mededelingen"]]
                .rename(columns={"Naam / Omschrijving":"Omschrijving","Bedrag_fmt":"Bedrag"}),
                use_container_width=True, hide_index=True,
            )
            sel = st.selectbox(
                "Selecteer voor correctie",
                range(len(review)),
                format_func=lambda i: (
                    f"{review.iloc[i]['Datum']} — "
                    f"{str(review.iloc[i]['Naam / Omschrijving'])[:40]} — "
                    f"{fmt_eur(review.iloc[i]['Bedrag'])}"
                ),
                key="pk_review_sel",
            )
            if st.button("✅ Markeer als Pokémon business", key="pk_review_btn"):
                st.session_state.corrections[review.iloc[sel]["tx_id"]] = "🃏 Pokémon business"
                st.success("Gecategoriseerd als Pokémon business"); st.rerun()
        else:
            st.success("✅ Geen verdachte transacties boven €15 gevonden.")


# ─────────────────────────────────────────────────────────────────
# PAGE 5 – ABONNEMENTEN & SLUIPENDE KOSTEN
# ─────────────────────────────────────────────────────────────────

def page_abonnementen(date_from, date_to, account_filter):
    st.title("🔍 Abonnementen & Sluipende Kosten")

    betaal = get_betaal(date_from, date_to, account_filter)
    if len(betaal) == 0:
        no_data(); return

    # Recurring = expenses appearing ≥3 times with same normalised name
    af = betaal[betaal["Af Bij"] == "Af"].copy()
    af["naam_norm"] = af["Naam / Omschrijving"].str.lower().str.strip().str[:40]

    agg = af.groupby("naam_norm").agg(
        count         = ("Bedrag", "count"),
        avg_bedrag    = ("Bedrag", "mean"),
        min_bedrag    = ("Bedrag", "min"),
        max_bedrag    = ("Bedrag", "max"),
        eerste_datum  = ("Datum",  "min"),
        laatste_datum = ("Datum",  "max"),
        naam_orig     = ("Naam / Omschrijving", "first"),
        categorie     = ("Categorie", "first"),
    ).reset_index()

    subs = agg[agg["count"] >= 3].copy()

    max_ts = pd.Timestamp(date_to)
    subs["actief"]      = (max_ts - subs["laatste_datum"]).dt.days <= 62
    subs["maanden"]     = ((subs["laatste_datum"] - subs["eerste_datum"]).dt.days / 30.4).clip(lower=1).round(0).astype(int)
    subs["maandbedrag"] = subs["avg_bedrag"]
    subs["jaarbedrag"]  = subs["maandbedrag"] * 12

    # ── Metrics ─────────────────────────────────────────────────
    actief = subs[subs["actief"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("📋 Actieve abonnementen",  len(actief))
    c2.metric("💸 Geschatte jaarkosten",  fmt_eur(actief["jaarbedrag"].sum()))
    c3.metric("📅 Gemiddeld per maand",   fmt_eur(actief["jaarbedrag"].sum() / 12))

    st.divider()

    # ── Overzichtstabel ─────────────────────────────────────────
    st.subheader("📋 Abonnementenoverzicht")
    disp = subs[["naam_orig","maandbedrag","jaarbedrag","eerste_datum","laatste_datum","actief","count"]].copy()
    disp["maandbedrag"]   = disp["maandbedrag"].apply(fmt_eur)
    disp["jaarbedrag"]    = disp["jaarbedrag"].apply(fmt_eur)
    disp["eerste_datum"]  = disp["eerste_datum"].dt.strftime("%d-%m-%Y")
    disp["laatste_datum"] = disp["laatste_datum"].dt.strftime("%d-%m-%Y")
    disp["actief"]        = disp["actief"].map({True: "✅ Actief", False: "⏸️ Inactief"})
    disp = disp.rename(columns={
        "naam_orig":     "Aanbieder",
        "maandbedrag":   "Maandbedrag",
        "jaarbedrag":    "Jaarbedrag",
        "eerste_datum":  "Eerste betaling",
        "laatste_datum": "Laatste betaling",
        "actief":        "Status",
        "count":         "# betalingen",
    })
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── Kostenstijgingen ────────────────────────────────────────
    st.subheader("⚠️ Kostenstijgingen")
    increases = []
    for _, row in subs.iterrows():
        sub_tx = af[af["naam_norm"] == row["naam_norm"]].sort_values("Datum")
        if len(sub_tx) < 6:
            continue
        early = sub_tx.head(3)["Bedrag"].mean()
        late  = sub_tx.tail(3)["Bedrag"].mean()
        if late > early * 1.05:
            increases.append({
                "Aanbieder":  row["naam_orig"],
                "Vroeger":    fmt_eur(early),
                "Nu":         fmt_eur(late),
                "Stijging":   fmt_eur(late - early),
                "Stijging %": f"+{(late/early - 1)*100:.1f}%",
            })
    if increases:
        st.dataframe(pd.DataFrame(increases), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Geen significante kostenstijgingen gedetecteerd.")

    # ── Jaarkosten per categorie ─────────────────────────────────
    st.subheader("📊 Jaarlijkse Abonnementskosten per Categorie")
    sub_names = set(subs["naam_norm"].values)
    sub_trans = af[af["naam_norm"].isin(sub_names)].copy()
    if len(sub_trans) > 0:
        n_months = max((pd.Timestamp(date_to) - pd.Timestamp(date_from)).days / 30.4, 1)
        cat_agg = (
            sub_trans.groupby("Categorie")["Bedrag"].sum() * (12 / n_months)
        ).reset_index()
        cat_agg.columns = ["Categorie", "Geschatte jaarbedrag"]
        fig = px.bar(
            cat_agg.sort_values("Geschatte jaarbedrag", ascending=False),
            x="Categorie", y="Geschatte jaarbedrag",
            title="Geschatte jaarlijkse abonnementskosten per categorie",
            template=PLOTLY_TEMPLATE, color_discrete_sequence=[COLOR_EXPENSE],
        )
        fig.update_layout(height=350, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    # ── Bezuinigingstips ────────────────────────────────────────
    st.subheader("💡 Bezuinigingstips")
    tips = actief[(actief["maandbedrag"] > 10) & (actief["maanden"] >= 12)].sort_values(
        "maandbedrag", ascending=False
    )
    if len(tips) > 0:
        for _, row in tips.iterrows():
            st.warning(
                f"**{row['naam_orig']}** — {fmt_eur(row['maandbedrag'])}/maand "
                f"({fmt_eur(row['jaarbedrag'])}/jaar) — "
                f"al ±{row['maanden']} maanden actief. Overweeg te heroverwegen!"
            )
    else:
        st.success("✅ Geen abonnementen die de bezuinigingsdrempel overschrijden.")


# ─────────────────────────────────────────────────────────────────
# PAGE 6 – MAAND-OP-MAAND VERGELIJKING
# ─────────────────────────────────────────────────────────────────

def page_maandvergelijking(date_from, date_to, account_filter):
    st.title("📅 Maand-op-maand Vergelijking")

    betaal = get_betaal(date_from, date_to, account_filter)
    if len(betaal) == 0:
        no_data(); return

    uitgaven = betaal[betaal["Af Bij"] == "Af"].copy()
    uitgaven["Maand"] = uitgaven["Datum"].dt.to_period("M").astype(str)
    alle_maanden = sorted(uitgaven["Maand"].unique().tolist())
    alle_cats    = sorted(uitgaven["Categorie"].unique().tolist())

    # ── Heatmap ─────────────────────────────────────────────────
    st.subheader("🌡️ Heatmap: Uitgaven per Maand × Categorie")
    hm = (
        uitgaven.groupby(["Maand","Categorie"])["Bedrag"].sum()
        .reset_index()
        .pivot(index="Categorie", columns="Maand", values="Bedrag")
        .fillna(0)
    )
    fig = go.Figure(data=go.Heatmap(
        z=hm.values,
        x=hm.columns.tolist(),
        y=hm.index.tolist(),
        colorscale="RdYlGn_r",
        hovertemplate="Categorie: %{y}<br>Maand: %{x}<br>Bedrag: €%{z:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE, height=max(400, len(alle_cats)*28),
        xaxis_title="Maand", yaxis_title="Categorie",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Twee maanden vergelijken ─────────────────────────────────
    st.subheader("📊 Twee Maanden Vergelijken")
    if len(alle_maanden) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            m1 = st.selectbox("Maand 1", alle_maanden, index=max(0, len(alle_maanden)-2))
        with c2:
            m2 = st.selectbox("Maand 2", alle_maanden, index=len(alle_maanden)-1)

        d1 = uitgaven[uitgaven["Maand"]==m1].groupby("Categorie")["Bedrag"].sum()
        d2 = uitgaven[uitgaven["Maand"]==m2].groupby("Categorie")["Bedrag"].sum()
        comp = pd.DataFrame({m1: d1, m2: d2}).fillna(0).reset_index()
        comp["Verschil"]   = comp[m2] - comp[m1]
        comp["Verschil %"] = comp.apply(
            lambda r: f"{'+' if r['Verschil']>=0 else ''}{(r['Verschil']/r[m1]*100):.1f}%"
                      if r[m1] > 0 else "N/A", axis=1
        )

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name=m1, x=comp["Categorie"], y=comp[m1], marker_color=COLOR_NEUTRAL))
        fig2.add_trace(go.Bar(name=m2, x=comp["Categorie"], y=comp[m2], marker_color="#9b59b6"))
        fig2.update_layout(
            template=PLOTLY_TEMPLATE, barmode="group", height=450,
            xaxis_tickangle=-30,
            title=f"Vergelijking {m1} vs {m2}",
        )
        st.plotly_chart(fig2, use_container_width=True)

        disp = comp.copy()
        disp[m1]          = disp[m1].apply(fmt_eur)
        disp[m2]          = disp[m2].apply(fmt_eur)
        disp["Verschil"]  = disp["Verschil"].apply(fmt_eur)
        st.dataframe(disp.rename(columns={"Categorie": "Categorie"}),
                     use_container_width=True, hide_index=True)

    st.divider()

    # ── Seizoenspatronen ────────────────────────────────────────
    st.subheader("🌊 Seizoenspatronen (afgelopen 24 maanden)")
    last24 = alle_maanden[-24:]
    seas   = uitgaven[uitgaven["Maand"].isin(last24)]
    avail  = sorted(seas["Categorie"].unique().tolist())
    sel    = st.multiselect(
        "Categorieën", avail,
        default=avail[:4] if len(avail) >= 4 else avail,
        key="seas_cats",
    )
    if sel:
        sd = seas[seas["Categorie"].isin(sel)].groupby(["Maand","Categorie"])["Bedrag"].sum().reset_index()
        fig3 = px.line(
            sd, x="Maand", y="Bedrag", color="Categorie", markers=True,
            title="Seizoenspatronen uitgaven per categorie", template=PLOTLY_TEMPLATE,
            labels={"Maand":"Maand","Bedrag":"Bedrag (€)"},
        )
        fig3.update_layout(height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    init_state()
    page, date_from, date_to, account_filter = sidebar()

    if page == "📊 Overzicht":
        page_overzicht(date_from, date_to, account_filter)
    elif page == "🛒 Uitgavencategorieën":
        page_categorieen(date_from, date_to, account_filter)
    elif page == "💰 Spaaranalyse":
        page_spaaranalyse(date_from, date_to, account_filter)
    elif page == "🃏 Pokémon P&L":
        page_pokemon(date_from, date_to, account_filter)
    elif page == "🔍 Abonnementen":
        page_abonnementen(date_from, date_to, account_filter)
    elif page == "📅 Maandvergelijking":
        page_maandvergelijking(date_from, date_to, account_filter)


if __name__ == "__main__":
    main()
