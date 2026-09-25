"""Cleans the raw traffic violations file and saves a clean CSV copy."""
import difflib
import re

import numpy as np
import pandas as pd
from pandas.api import types as ptypes

# Don't truncate wide output when printing the DataFrame.
pd.set_option("display.max_columns", None)

# Accepted tokens for a Yes/No-style boolean column.
BOOLEAN_VOCAB = {"YES", "NO", "Y", "N", "TRUE", "FALSE"}


def detect_boolean_columns(df):
    """Return columns whose values are all Yes/No-style booleans (incl. nullable bool dtype)."""
    detected = []
    for col in df.columns:
        series = df[col]
        if ptypes.is_bool_dtype(series.dtype):
            detected.append(col)
            continue
        non_null = series.dropna().astype(str).str.upper().str.strip()
        if not non_null.empty and set(non_null.unique()) <= BOOLEAN_VOCAB:
            detected.append(col)
    return detected


# Columns handled specially (dates, coords, Year, Make, IDs, dropped) - excluded from generic text cleaning.
SPECIAL_HANDLING_COLUMNS = {
    "SeqID", "Date Of Stop", "Time Of Stop", "Latitude", "Longitude",
    "Year", "Make", "Geolocation",
}


def detect_text_columns(df, boolean_columns):
    """Return the remaining generic text columns (object or string dtype)."""
    detected = []
    for col in df.columns:
        if col in SPECIAL_HANDLING_COLUMNS or col in boolean_columns:
            continue
        if df[col].dtype == object or str(df[col].dtype) in (
            "str", "string"
        ):
            detected.append(col)
    return detected


# Canonical car brands used to correct Make typos/abbreviations.
CANONICAL_MAKES = [
    "ACURA", "ALFA ROMEO", "AMC", "ASTON MARTIN", "AUDI", "BENTLEY", "BMW",
    "BUICK", "CADILLAC", "CHEVROLET", "CHRYSLER", "CITROEN", "DAEWOO",
    "DODGE", "FERRARI", "FIAT", "FORD", "FREIGHTLINER", "GENESIS", "GMC",
    "HARLEY-DAVIDSON", "HONDA", "HUMMER", "HYUNDAI", "INFINITI", "ISUZU",
    "JAGUAR", "JEEP", "KAWASAKI", "KIA", "LAMBORGHINI", "LAND ROVER",
    "LEXUS", "LINCOLN", "LOTUS", "MASERATI", "MAZDA", "MCLAREN",
    "MERCEDES-BENZ", "MERCURY", "MINI", "MITSUBISHI", "NISSAN",
    "OLDSMOBILE", "PEUGEOT", "PLYMOUTH", "PONTIAC", "PORSCHE", "RAM",
    "RENAULT", "ROLLS-ROYCE", "SAAB", "SATURN", "SCION", "SMART",
    "SUBARU", "SUZUKI", "TESLA", "TOYOTA", "TRIUMPH", "VOLKSWAGEN",
    "VOLVO", "YAMAHA", "KTM", "DUCATI",
    "INTERNATIONAL", "MACK", "HINO", "PETERBILT", "KENWORTH", "GEO",
    "GILLIG", "NEW FLYER", "THOMAS BUILT", "RIVIAN",
]
# Nicknames/typos too short or misspelt for standardize_make's matching rules.
MAKE_NICKNAMES = {
    "CHEVY": "CHEVROLET", "TOYT": "TOYOTA",
    "ACRUA": "ACURA", "AUCRA": "ACURA", "BWM": "BMW",
    "MERZ": "MERCEDES-BENZ", "BENZ": "MERCEDES-BENZ",
    "MERCEDEZ": "MERCEDES-BENZ", "VW": "VOLKSWAGEN", "TOY": "TOYOTA",
    "ISU": "ISUZU", "CAD": "CADILLAC", "STRN": "SATURN",
    "LNDR": "LAND ROVER", "FRHT": "FREIGHTLINER", "MNNI": "MINI",
    "SUZI": "SUZUKI", "MITZ": "MITSUBISHI", "KW": "KENWORTH",
    "INTL": "INTERNATIONAL",
    "MINI COOPER": "MINI", "RANGE ROVER": "LAND ROVER",
    "PTRB": "PETERBILT", "LEX": "LEXUS", "RANGE": "LAND ROVER",
    "RANG": "LAND ROVER", "CHEVERLOT": "CHEVROLET", "IZUZU": "ISUZU",
    "SUB": "SUBARU", "SUBU": "SUBARU", "JAG": "JAGUAR",
    "KAWK": "KAWASAKI", "MITTS": "MITSUBISHI",
    "VOLTSWAGON": "VOLKSWAGEN", "HINDA": "HONDA", "HYND": "HYUNDAI",
    "INFINTY": "INFINITI", "SATR": "SATURN", "CHEY": "CHEVROLET",
    "LEXIS": "LEXUS", "LEXAS": "LEXUS", "LUXUS": "LEXUS",
    "HON": "HONDA", "MERZ BENZ": "MERCEDES-BENZ", "HUYN": "HYUNDAI",
    "HUNDAY": "HYUNDAI", "MERECEDES": "MERCEDES-BENZ", "SUZ": "SUZUKI",
    "MADZA": "MAZDA", "CADALLIC": "CADILLAC", "MIT": "MITSUBISHI",
    "COOPER": "MINI",
    "MERC. BENZ": "MERCEDES-BENZ", "MERCEDEZ/AMG": "MERCEDES-BENZ",
    "TOWN & COUNTRY": "CHRYSLER", "TOYT (SCION)": "TOYOTA",
    "!2010HONDA": "HONDA", "MITSUH": "MITSUBISHI",
}
# Brief's literal year bounds - fixed, not a rolling cutoff.
MIN_VALID_YEAR = 1960
MAX_VALID_YEAR = 2025
# Earliest plausible Date Of Stop year (digital records start ~2012; file min is 2012-01-01).
MIN_VALID_STOP_YEAR = 2000
# Search columns blanked to "Not Applicable" when no search was conducted.
SEARCH_NOT_APPLICABLE_COLUMNS = [
    "Search Outcome", "Search Type", "Search Reason For Stop",
    "Search Reason", "Search Arrest Reason",
]
# Same pattern, but the brief specifies "NA" for this column instead.
SEARCH_NA_COLUMN = "Search Disposition"
# "XX"/"US" mean "not specified"; real foreign codes are kept.
STATE_COLUMNS = ["State", "Driver State", "DL State"]
INVALID_STATE_CODES = ["XX", "US"]
# Text duplicate of Latitude/Longitude - dropped instead of cleaned twice.
REDUNDANT_COLUMNS = ["Geolocation"]
# The only two Color values abbreviating DARK/LIGHT.
COLOR_MAP = {"GREEN, DK": "GREEN, DARK", "GREEN, LGT": "GREEN, LIGHT"}
# 190 hand-verified typos of real places (e.g. "BEHTESDA" -> "BETHESDA").
DRIVER_CITY_MAP = {
    "0XON HILL": "OXON HILL", "ADELHPI": "ADELPHI", "ADELPH": "ADELPHI",
    "ADELPHUI": "ADELPHI", "ADELPI": "ADELPHI", "ARILINGTON": "ARLINGTON",
    "ARKINGTON": "ARLINGTON", "ARLINGTON4": "ARLINGTON",
    "ARLLINGTON": "ARLINGTON", "ASBURN": "ASHBURN", "AUREL": "LAUREL",
    "BAILTIMORE": "BALTIMORE", "BALTAMORE": "BALTIMORE",
    "BALTIOMORE": "BALTIMORE", "BALTMORE": "BALTIMORE",
    "BEALLESVILLE": "BEALLSVILLE", "BEHTESDA": "BETHESDA",
    "BELSTVILLE": "BELTSVILLE", "BELTESVILLE": "BELTSVILLE",
    "BELTSBILLE": "BELTSVILLE", "BELTSVILE": "BELTSVILLE",
    "BELTSVILL": "BELTSVILLE", "BELTVILLE": "BELTSVILLE",
    "BERWIN HEIGHTS": "BERWYN HEIGHTS", "BESTHEDA": "BETHESDA",
    "BETHESDAS": "BETHESDA", "BETHESDSA": "BETHESDA",
    "BETHSDA": "BETHESDA", "BEWTHESDA": "BETHESDA",
    "BLADENSBURN": "BLADENSBURG", "BOISE": "BOWIE", "BOUIE": "BOWIE",
    "BOYS": "BOYDS",
    "BRADDOCK HIGHTS": "BRADDOCK HEIGHTS", "BRANDWINE": "BRANDYWINE",
    "BRENTOOD": "BRENTWOOD", "BRLTSVILLE": "BELTSVILLE",
    "BRTHESDA": "BETHESDA", "BUERTONSVILLE": "BURTONSVILLE",
    "BURTNOSVILLE": "BURTONSVILLE", "BURTONSIVLLE": "BURTONSVILLE",
    "BURTONSVIILLE": "BURTONSVILLE", "BURTONSVLLE": "BURTONSVILLE",
    "BURTONVILLE": "BURTONSVILLE", "BURTOSNSVILLE": "BURTONSVILLE",
    "BURTSONSVILLE": "BURTONSVILLE", "CAPTIAL HEIGHTS": "CAPITAL HEIGHTS",
    "CCOLLEGE PARK": "COLLEGE PARK", "CHARLOTTESVILLS": "CHARLOTTESVILLE",
    "CHERVY CHASE": "CHEVY CHASE", "CHEVY CHAS": "CHEVY CHASE",
    "CHEVY CHASEE": "CHEVY CHASE", "CHEY CHASE": "CHEVY CHASE",
    "CINNCINATI": "CINCINNATI", "CLAKRSBURG": "CLARKSBURG",
    "CLARKBURG": "CLARKSBURG", "CLARKESBURG": "CLARKSBURG",
    "CLARKSBUURG": "CLARKSBURG", "CLARSBURG": "CLARKSBURG",
    "CLARSKBURG": "CLARKSBURG", "COILLEGE PARK": "COLLEGE PARK",
    "COLEEGE PARK": "COLLEGE PARK", "COLEGE PARK": "COLLEGE PARK",
    "COLLAGE PARK": "COLLEGE PARK", "COLOMBUS": "COLUMBUS",
    "CROWNVILLE": "CROWNSVILLE", "CULPEPEPER": "CULPEPER",
    "DAMACSUS": "DAMASCUS", "DAMACUS": "DAMASCUS", "DAMASVUS": "DAMASCUS",
    "DMASCUS": "DAMASCUS", "DOWIE": "BOWIE", "DUMPHRIES": "DUMFRIES",
    "DURHAMNC": "DURHAM", "ELKONS": "ELKTON", "ELKRDIGE": "ELKRIDGE",
    "FAIFAX": "FAIRFAX", "FAIRFA": "FAIRFAX",
    "FALLS CHRUCH": "FALLS CHURCH",
    "FAMIRMONT HEIGHTS": "FAIRMOUNT HEIGHTS",
    "FAYETTESVILLE": "FAYETTEVILLE", "FINKBURG": "FINKSBURG",
    "FREDERICKBURG": "FREDERICKSBURG", "FREDRICKSBURG": "FREDERICKSBURG",
    "GAINSVILLE": "GAINESVILLE", "GAITHERSRBUG": "GAITHERSBURG",
    "GARRET PARK": "GARRETT PARK", "GCLARKSBURG": "CLARKSBURG",
    "GELNMONT": "GLENMONT", "GERMATNOWN": "GERMANTOWN",
    "GERMNATOWN": "GERMANTOWN", "GLEN  BURNIE": "GLEN BURNIE",
    "GLEN ARDEN": "GLENARDEN", "GLEN BOURNIE": "GLEN BURNIE",
    "GWYNN OAKS": "GWYNN OAK", "GYWNN OAK": "GWYNN OAK",
    "HAFERSTOWN": "HAGERSTOWN", "HAGERSTOEN": "HAGERSTOWN",
    "HAGERTOWN": "HAGERSTOWN", "HERDON": "HERNDON",
    "HYAATTSVILLLE": "HYATTSVILLE", "KENNSINGTON": "KENSINGTON",
    "KENSIGNTON": "KENSINGTON", "KENSINGTO": "KENSINGTON",
    "KENSINGTOM": "KENSINGTON", "KENSINTON": "KENSINGTON",
    "KENSNGTON": "KENSINGTON", "KENSSINGTON": "KENSINGTON",
    "KISSIMME": "KISSIMMEE", "LANDHAM": "LANHAM", "LARUEL": "LAUREL",
    "LAUERL": "LAUREL", "LAURL": "LAUREL", "LAYTONSVILE": "LAYTONSVILLE",
    "LAYTONVILLE": "LAYTONSVILLE", "LEMONT": "GLENMONT",
    "LEXINTON PARK": "LEXINGTON PARK", "LNFALLS CHURCH": "FALLS CHURCH",
    "MAMASSASS": "MANASSAS", "MANASAS": "MANASSAS",
    "MANASASS": "MANASSAS", "MANASSASS": "MANASSAS",
    "MANNASSAS": "MANASSAS", "MARRIOTSVILLE": "MARRIOTTSVILLE",
    "MARTINBURG": "MARTINSBURG", "MECHANICSVLLE": "MECHANICSVILLE",
    "MICHELLVILLE": "MITCHELLVILLE", "MIDDLEOWN": "MIDDLETOWN",
    "MITCHELVILLE": "MITCHELLVILLE", "MITCHEVILLE": "MITCHELLVILLE",
    "MKIDDLETOWN": "MIDDLETOWN", "MONROVA": "MONROVIA",
    "MONTGOMERY VILLAGE A": "MONTGOMERY VILLAGE", "MONTOVIA": "MONROVIA",
    "MOTNGOMERY VILLAGE": "MONTGOMERY VILLAGE",
    "MOUNTY AIRY": "MOUNT AIRY", "MT.  AIRY": "MT AIRY",
    "MTAIRY": "MT AIRY", "NOTTIINGHAM": "NOTTINGHAM", "OLNET": "OLNEY",
    "OWENS MILLS": "OWINGS MILLS", "OXEN HILL": "OXON HILL",
    "PHILADEPHIA": "PHILADELPHIA", "PITTSBURG": "PITTSBURGH",
    "POINT OF ROCK": "POINT OF ROCKS",
    "POOLSEVILLE": "POOLESVILLE", "POOMAC": "POTOMAC",
    "PORT OF ROCKS": "POINT OF ROCKS", "POTAOMC": "POTOMAC",
    "POTOMA": "POTOMAC", "POTOMAAC": "POTOMAC", "POTOMC": "POTOMAC",
    "POTOMMAC": "POTOMAC", "POTOMOAC": "POTOMAC", "POTOMOC": "POTOMAC",
    "POTOPMAC": "POTOMAC", "POTPMAC": "POTOMAC",
    "PRINCESS ANN": "PRINCESS ANNE", "PURCELVILLE": "PURCELLVILLE",
    "QLNEY": "OLNEY", "REISERTOWN": "REISTERSTOWN",
    "REISTERTOWN": "REISTERSTOWN", "RESITERSTOWN": "REISTERSTOWN",
    "ROCKVILLE F": "ROCKVILLE", "ROCKVILLE P": "ROCKVILLE",
    "ROSDALE": "ROSEDALE", "RVERDALE": "RIVERDALE",
    "SANDY SPRNIG": "SANDY SPRING",
    "SEAT PLEASNT": "SEAT PLEASANT", "SNADY SPRING": "SANDY SPRING",
    "SPRINFIELD": "SPRINGFIELD", "SPRNGFIELD": "SPRINGFIELD",
    "SPRONGFIELD": "SPRINGFIELD", "STAEN ISLAND": "STATEN ISLAND",
    "STAFORD": "STAFFORD", "TAKOMA PK": "TAKOMA PARK",
    "THURMONY": "THURMONT", "TIMIMONIUM": "TIMONIUM",
    "UPPERMARLBORO": "UPPER MARLBORO", "UPPR MARLBORO": "UPPER MARLBORO",
    "UPR MARLBORO": "UPPER MARLBORO", "URBABA": "URBANA",
    "WALDORPH": "WALDORF", "WASHINGTON, D.C.": "WASHINGTON D.C.",
    "WASHINGTON, DC": "WASHINGTON DC", "WESTMINISTER": "WESTMINSTER",
    "WHEATORN": "WHEATON", "WINDSOR MILLS": "WINDSOR MILL",
    "WINSOR MILL": "WINDSOR MILL", "YUNKERS": "YONKERS",
}
# Placeholder values that describe nothing real.
PLACEHOLDER_VALUES = [
    "NONE", "UNKNOWN", "UNK", "XX", "N/A", "NA", "0", "[UNKNOWN]",
]
PLACEHOLDER_COLUMNS = ["Make", "Model", "Driver City", "Article", "Color"]
# "CODE - Description" columns split into code + description (original kept).
CODE_SPLIT_COLUMNS = {
    "VehicleType": ("VehicleType Code", "VehicleType Category"),
    "Arrest Type": ("Arrest Type Code", "Arrest Type Description"),
}
# Valid legal codes have an article-dash-section shape (e.g. "13-401(b1)").
LEGAL_CODE_COLUMNS = ["Charge", "Search Reason For Stop"]
# 366 verified model typos, scoped by each vehicle's Make.
MODEL_CORRECTIONS = {
    "ACURA": {
        "INTREGA": "INTEGRA",
    },
    "BUICK": {
        "CENTRUY": "CENTURY", "CONCLAVE": "ENCLAVE", "ENCLACE": "ENCLAVE",
        "LACOSSE": "LACROSSE", "LACROSE": "LACROSSE",
        "LACROSS": "LACROSSE", "LECROSSE": "LACROSSE",
        "LESABER": "LESABRE", "LUCERINE": "LUCERNE", "ONCLAVE": "ENCLAVE",
        "VERAND": "VERANO",
    },
    "CADILLAC": {
        "EL DORADO": "ELDORADO", "ELDDRADO": "ELDORADO",
        "ESCALDE": "ESCALADE", "ESCALLADE": "ESCALADE",
        "ESCELADE": "ESCALADE", "ESCLADE": "ESCALADE",
        "ESCUADE": "ESCALADE",
    },
    "CHEVROLET": {
        "AVALANCE": "AVALANCHE", "BLAZOR": "BLAZER",
        "CAVALER": "CAVALIER", "CAVALERE": "CAVALIER",
        "CAVELER": "CAVALIER", "COLOORADO": "COLORADO",
        "IMPAL;A": "IMPALA",
        "CORVETEE": "CORVETTE", "CORVETTTE": "CORVETTE",
        "EQIINUX": "EQUINOX", "EQUIINOX": "EQUINOX", "EQUIN": "EQUINOX",
        "EQUINOIX": "EQUINOX", "EQUINOK": "EQUINOX", "EQUINON": "EQUINOX",
        "EQUINOZ": "EQUINOX", "EQUNOX": "EQUINOX", "IMPL": "IMPALA",
        "M VAN": "VAN", "SILVERRODO": "SILVERADO", "SUBRUBAN": "SUBURBAN",
        "SUBUBAN": "SUBURBAN", "SUBURBAM": "SUBURBAN",
        "SUBURVAN": "SUBURBAN", "SURBUBAN": "SUBURBAN",
        "SURBURBAN": "SUBURBAN", "TAGOE": "TAHOE", "TAHHOE": "TAHOE",
        "TAHO": "TAHOE", "THAHO": "TAHOE", "TRANVERSE": "TRAVERSE",
        "TRTEVERSE": "TRAVERSE", "TRUCJ": "TRUCK", "VAN20": "VAN",
        "W VAN": "VAN", "WQUINOX": "EQUINOX",
    },
    "CHRYSLER": {
        "LA BARON": "LEBARON", "PT-CRUISER": "PT CRUISER",
        "PTCRUISER": "PT CRUISER", "YOYAGER": "VOYAGER",
    },
    "DODGE": {
        "AVENFER": "AVENGER", "CAERAVAN": "CARAVAN", "CALIBUR": "CALIBER",
        "CALIER": "CALIBER", "CARAVA": "CARAVAN", "CARAVAN`": "CARAVAN",
        "CARIVAN": "CARAVAN", "CARRAVAN": "CARAVAN", "CHAEGER": "CHARGER",
        "CHALLEGER": "CHALLENGER", "CHANGLER": "CHARGER",
        "CHARG": "CHARGER", "CHARGE": "CHARGER", "CHRAGER": "CHARGER",
        "DERANGO": "DURANGO", "DOKOTA": "DAKOTA", "DURANGI": "DURANGO",
        "DURANGOW": "DURANGO", "DURGANGO": "DURANGO",
        "INTREP": "INTREPID", "INTREPED": "INTREPID",
        "JORNERY": "JOURNEY", "JORNEY": "JOURNEY", "PICK - UP": "PICK UP",
        "RAM/VAN": "RAM VAN", "STARTUS": "STRATUS", "STATUS": "STRATUS",
        "W VAN": "VAN",
    },
    "FORD": {
        "AEROSTA": "AEROSTAR", "BOXTRUCK": "BOX TRUCK",
        "BRANCO": "BRONCO", "C MAX": "CMAX", "C-MAX": "CMAX",
        "CONTOR": "CONTOUR", "CROWNVIC": "CROWN VIC",
        "CROWNVICTORIA": "CROWN VICTORIA", "ECO SPORT": "ECOSPORT",
        "EPEDITION": "EXPEDITION", "ESCAPEE": "ESCAPE",
        "EXP;ORER": "EXPLORER", "EXPEDITIOIN": "EXPEDITION",
        "EXPEDITITON": "EXPEDITION", "EXPIDEITION": "EXPEDITION",
        "EXPIORER": "EXPLORER", "EXPLOER": "EXPLORER",
        "EXPLORR": "EXPLORER", "EXPLOYER": "EXPLORER",
        "EXPOLRER": "EXPLORER", "F PICKUP": "PICKUP", "FESDTA": "FIESTA",
        "FESTA": "FIESTA", "FLX": "FLEX", "FOCUZ": "FOCUS",
        "FUDION": "FUSION", "FUSHION": "FUSION", "FUSIAN": "FUSION",
        "FUSON": "FUSION", "MUSSTANG": "MUSTANG", "MUSTAND": "MUSTANG",
        "MUSTANF": "MUSTANG", "MUSTANGE": "MUSTANG", "MUSTANT": "MUSTANG",
        "TRANIST": "TRANSIT", "TRASIT": "TRANSIT", "W VAN": "VAN",
        "[SD]": "SD",
    },
    "GEO": {
        "PRIZIT": "PRIZM",
    },
    "GMC": {
        "A ADIA": "ACADIA", "ACARDIA": "ACADIA", "ACCADIA": "ACADIA",
        "ACRDIA": "ACADIA", "CANTON": "CANYON", "DENILLI": "DENALI",
        "ENVY": "ENVOY", "PICK UP": "PICKUP", "SAVAVA": "SAVANA",
        "SONMA": "SONOMA", "TERAIN": "TERRAIN", "TERRAI N": "TERRAIN",
        "TERRANE": "TERRAIN", "TERRIN": "TERRAIN", "TEWRRAIN": "TERRAIN",
        "W VAN": "VAN", "YOKON": "YUKON", "YUCON": "YUKON",
        "YURON": "YUKON",
    },
    "HONDA": {
        "200Z": "S2000", "CR V SUV": "CRV SUV", "CROSS TOUR": "CROSSTOUR",
        "CROSTOUR": "CROSSTOUR", "ELEMNET": "ELEMENT", "FIRT": "FIT",
        "M VAN": "VAN", "MOTOR CYCLE": "MOTORCYCLE", "PIILOT": "PILOT",
        "PILO": "PILOT", "PIOL": "PILOT", "PIOLOT": "PILOT",
        "PIOLT": "PILOT", "PLIOT": "PILOT", "RUCKAS": "RUCKUS",
        "RUCUS": "RUCKUS", "VAN ODYSSEY": "VN/ODYSSEY",
        "VN ODYSSEY": "VN/ODYSSEY",
    },
    "HYUNDAI": {
        "ACCDENT": "ACCENT", "ACEENT": "ACCENT", "ACENT": "ACCENT",
        "ACERA": "AZERA", "AZRA": "AZERA", "CERACRUZ": "VERACRUZ",
        "ELANRTA": "ELANTRA", "ELANTRARA": "ELANTRA", "EZERA": "AZERA",
        "KNOA": "KONA", "KONO": "KONA", "PALISADES": "PALISADE",
        "SOMAT": "SONATA", "SONATAWI": "SONATA", "TIBERON": "TIBURON",
        "VENU": "VENUE", "VERA CRUZ": "VERACRUZ", "VERROCRUZ": "VERACRUZ",
        "VOLSTER": "VELOSTER",
    },
    "JEEP": {
        "GLADIATOT": "GLADIATOR", "LADEDO": "LAREDO", "LARADO": "LAREDO",
        "LATITUDED": "LATITUDE", "LATUTUDE": "LATITUDE",
        "LIBERT": "LIBERTY", "LIMTED": "LIMITED", "LMITED": "LIMITED",
        "PATIROT": "PATRIOT", "PATROIT": "PATRIOT", "RANGLER": "WRANGLER",
        "RENAGADE": "RENEGADE", "RENGADE": "RENEGADE",
        "WEANGLER": "WRANGLER", "WRANGELER": "WRANGLER",
        "WRANGLER`": "WRANGLER", "WRANGLR": "WRANGLER",
    },
    "KAWASAKI": {
        "NIJA": "NINJA",
    },
    "KENWORTH": {
        "DUMPTRUCK": "DUMP TRUCK",
    },
    "KIA": {
        "FORTED": "FORTE", "FORTTE": "FORTE", "M VAN": "VAN",
        "OPTMIA": "OPTIMA", "POTIMA": "OPTIMA", "RONOC": "RONDO",
        "SEDONDA": "SEDONA", "SEDORA": "SEDONA", "SELTOA": "SELTOS",
        "SORETNO": "SORENTO", "SOULD": "SOUL", "SPECTRS": "SPECTRA",
        "SPROTAGE": "SPORTAGE", "STINNGER": "STINGER",
        "TEELLURIDE": "TELLURIDE", "TELARIDE": "TELLURIDE",
        "TELURIDE": "TELLURIDE", "TILLURIDE": "TELLURIDE",
    },
    "LEXUS": {
        "GS300`": "GS300",
    },
    "LINCOLN": {
        "CONTINTENTAL": "CONTINENTAL", "NAVAGATOR": "NAVIGATOR",
        "NAVIGATIOR": "NAVIGATOR", "NEAVIGATOR": "NAVIGATOR",
    },
    "MAZDA": {
        "3`": "3", "MAZ6": "MAZDA6", "MIATTA": "MIATA",
        "MILLINEA": "MILLENIA", "TKCX5": "CX5",
    },
    "MITSUBISHI": {
        "CADEAVOR": "ENDEAVOR", "DIAMENTE": "DIAMANTE",
        "ECLIPES": "ECLIPSE", "ECLIPLSE": "ECLIPSE", "ECLIPS": "ECLIPSE",
        "ECLPISE": "ECLIPSE", "ECPLIPSE": "ECLIPSE", "ECPLISE": "ECLIPSE",
        "EWNDEAVOR": "ENDEAVOR", "GALA": "GALANT", "LANCE": "LANCER",
        "LANCHER": "LANCER", "MONTARO": "MONTERO", "MURAGE": "MIRAGE",
        "OUT;LANDER": "OUTLANDER", "OUTLA NDER": "OUTLANDER",
        "SPIDER": "SPYDER",
    },
    "NISSAN": {
        "2S ~350Z": "350Z", "AEMADA": "ARMADA", "ALTIMAAN": "ALTIMA",
        "ATLIMA": "ALTIMA", "CENTRA": "SENTRA", "CP ~350Z": "350Z",
        "FRONTER": "FRONTIER", "GT R": "GTR",
        "VERSA`": "VERSA",
        "MARANO": "MURANO", "MAXINA": "MAXIMA", "MIRANO": "MURANO",
        "MURADA": "MURANO", "MURANLO": "MURANO", "MURRAND": "MURANO",
        "MURRANO": "MURANO", "NAXIMA": "MAXIMA",
        "PATFINDER": "PATHFINDER", "PATHFINGER": "PATHFINDER",
        "PATHJFGINDER": "PATHFINDER", "QWEST": "QUEST", "RAGOUE": "ROGUE",
        "SE NTRA": "SENTRA", "SENRTA": "SENTRA", "SENTRAA": "SENTRA",
        "SENTRTA": "SENTRA", "SENYRA": "SENTRA", "TKROGUE": "ROGUE",
        "VENNA": "VERSA", "VERZA": "VERSA", "W VAN": "VAN",
    },
    "OLDSMOBILE": {
        "SILOUETTE": "SILHOUETTE",
    },
    "PLYMOUTH": {
        "VOYOGER": "VOYAGER",
    },
    "PONTIAC": {
        "GRAN D AM": "GRAND AM", "GRAND-AM": "GRAND AM",
    },
    "PORSCHE": {
        "BOXTER": "BOXSTER", "CARRARA": "CARRERA", "CARRERRA": "CARRERA",
        "CASPENNE": "CAYENNE", "CAYANNE": "CAYENNE", "CAYENE": "CAYENNE",
        "CAYENEE": "CAYENNE", "CHAYENNE": "CAYENNE", "CYANNE": "CAYENNE",
        "MACCAN": "MACAN", "PANAMARA": "PANAMERA",
    },
    "RAM": {
        "POMASTER": "PROMASTER", "PRO MASTER": "PROMASTER",
        "PROMAST": "PROMASTER", "PROMSTER": "PROMASTER",
    },
    "SATURN": {
        "YAURA": "AURA",
    },
    "SCION": {
        "2 DR": "2D",
    },
    "SUBARU": {
        "ACCSENT": "ASCENT", "CROSSTEK": "CROSSTREK",
        "CROSSTEX": "CROSSTREK", "CROSSTREKI": "CROSSTREK",
        "CROSSTREX": "CROSSTREK", "CROSSTRK": "CROSSTREK",
        "CROSTREK": "CROSSTREK", "ELGACY": "LEGACY", "FOREST": "FORESTER",
        "IMPEZA": "IMPREZA", "IMPLAZA": "IMPREZA", "IMPRE": "IMPREZA",
        "IMPRESSA": "IMPREZA", "IMPREZ": "IMPREZA", "IMPREZO": "IMPREZA",
        "IMPTEZA": "IMPREZA", "IMREZA": "IMPREZA", "LEACY": "LEGACY",
        "LEGACT": "LEGACY", "OATBACK": "OUTBACK", "OUOTBACK": "OUTBACK",
        "OUTBAXK": "OUTBACK",
    },
    "SUZUKI": {
        "GX600": "GSXR600", "SXL-7": "XL7",
    },
    "TOYOTA": {
        "4RUNN": "4RUNNER", ";PRIUS": "PRIUS", "ACION": "SCION",
        "AVALO": "AVALON", "AVALONE": "AVALON", "AVOLON": "AVALON",
        "AVVALON": "AVALON", "CECILCA": "CELICA", "CELLICA": "CELICA",
        "CSION": "SCION", "FJCRUISER": "FJ CRUISER",
        "G HIGHLANDER": "HIGHLANDER", "GRHIGHLANDER": "HIGHLANDER",
        "LANDCRUSIER": "LANDCRUISER", "MINI VAN": "MINIVAN",
        "MR2``": "MR2", "ORIUS": "PRIUS", "P/\\U": "PU", "PPRIUS": "PRIUS",
        "PREVA": "PREVIA", "PRIOUS": "PRIUS", "PRIUA": "PRIUS",
        "SADAN": "SEDAN", "SEANNA": "SIENNA", "SERQUOIA": "SEQUOIA",
        "SOLARES": "SOLARA", "SOLORA": "SOLARA", "T1OO": "T100",
        "TECEL": "TERCEL", "TERCELL": "TERCEL", "TERECEL": "TERCEL",
        "TKTACOMA": "TACOMA", "TOYT": "TOYOTA", "TUBDRA": "TUNDRA",
        "TUNDR": "TUNDRA", "TUNTRA": "TUNDRA", "VARIS": "YARIS",
        "VARRIS": "YARIS", "VENCA": "VENZA", "VENEA": "VENZA",
        "VENGA": "VENZA", "VN/SIENNA": "VN SIENNA", "YAARIS": "YARIS",
        "YURIS": "YARIS",
    },
    "VOLKSWAGEN": {
        "ATLIS": "ATLAS", "E05": "EOS", "JETA": "JETTA",
        "JETTAS": "JETTA", "JETTS": "JETTA", "KETTA": "JETTA",
        "PAASAT": "PASSAT", "PASAT": "PASSAT", "PASSAAT": "PASSAT",
        "PASSDAT": "PASSAT", "PASSET": "PASSAT", "TIGUAH": "TIGUAN",
        "TIQUAN": "TIGUAN", "TITIGUAN": "TIGUAN", "TOVARES": "TOUAREG",
    },
    "ZHEJIANG": {
        "TRANS PRO": "TRANSPRO",
    },
}
# Description keyword groups, first match wins (order matters: LICENSE PLATE before LICENSE).
VIOLATION_CATEGORY_KEYWORDS = [
    ("REGISTRATION", ["LICENSE PLATE", "REGISTRATION", "REGISTERED"]),
    ("SPEEDING", ["SPEED"]),
    ("LICENSE", ["LICENSE"]),
    ("ALCOHOL/DUI", ["ALCOHOL", "DUI", "DWI", "IMPAIRED", "INFLUENCE"]),
    ("TRAFFIC CONTROL DEVICE",
     ["TRAFFIC CONTROL", "STOP SIGN", "RED SIGNAL", "TRAFFIC SIGNAL"]),
    ("CELL PHONE", ["TELEPHONE", "HANDHELD", "CELLULAR"]),
    ("CARELESS/NEGLIGENT", ["NEGLIGENT", "CARELESS", "RECKLESS"]),
    ("LANE CHANGE", ["LANE"]),
    ("SEAT BELT", ["SEAT BELT", "SEATBELT", "CHILD RESTRAINT"]),
    ("INSURANCE", ["INSURANCE", "SECURITY"]),
]


def print_dtypes_check(df):
    """Print the dtype pandas assigned to every column on load, before any cleaning."""
    print("dtypes, as read from the raw file (before any cleaning):")
    print(df.dtypes)


def describe_raw_data(df):
    """Print a first look at the raw data: shape, dtypes, sample rows and summary stats."""
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print()
    print("--- dtypes ---")
    print(df.dtypes)
    print()
    print("--- head ---")
    print(df.head())
    print()
    print("--- info ---")
    df.info()
    print()
    print("--- describe (numeric columns) ---")
    print(df.describe())
    print()
    print("--- describe (all columns, incl. text) ---")
    print(df.describe(include="all"))


def load_data(path):
    """Read the raw file (Excel or CSV); raise a clear error if it fails."""
    try:
        if path.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(path)
        return pd.read_csv(path, low_memory=False)
    except FileNotFoundError:
        print(f"ERROR: '{path}' not found.")
        raise
    except Exception as error:
        print(f"ERROR while reading '{path}': {error}")
        raise


def _clean(series, upper=True):
    """Trim, collapse internal whitespace, and set case - shared by every text cleaner."""
    series = series.astype(str).str.replace(r"\s+", " ", regex=True)
    series = series.str.strip()
    return series.str.upper() if upper else series.str.lower()


def print_boolean_missing_summary(df, boolean_columns):
    """Print the detected boolean columns and their missing-value counts, highest first."""
    print(f"Detected {len(boolean_columns)} boolean columns:")
    print(boolean_columns)
    print("Missing values per boolean column (highest first):")
    print(df[boolean_columns].isna().sum().sort_values(ascending=False))


def print_search_conducted_relatedness(df, boolean_columns):
    """Print, per other boolean column, the Search Conducted Yes-rate gap and smallest group size."""
    if "Search Conducted" not in df.columns:
        return
    known = df.dropna(subset=["Search Conducted"])
    candidates = [c for c in boolean_columns if c != "Search Conducted"]
    rows = []
    for col in candidates:
        rate = known.groupby(col, observed=True)["Search Conducted"].apply(
            lambda values: (values == "Yes").mean() * 100
        )
        smallest_group = known[col].value_counts().min()
        rows.append((col, rate.max() - rate.min(), smallest_group))
    rows.sort(key=lambda row: row[1], reverse=True)
    print(
        "Search Conducted Yes-rate gap by column "
        "(big gap + big smallest-group = trustworthy, related column):"
    )
    for col, gap, smallest_group in rows:
        print(
            f"  {col:24s} gap={gap:5.1f}pp   "
            f"smallest group n={smallest_group}"
        )


# Columns with a real Yes-rate gap AND a large-enough sample used to fill Search Conducted.
SEARCH_CONDUCTED_GROUP_COLUMNS = [
    "Alcohol", "Property Damage", "Accident",
]


def fill_search_conducted_by_group(df, boolean_columns, verbose=False):
    """Fill missing Search Conducted from the mode within each group column (before clean_yes_no)."""
    if "Search Conducted" not in df.columns:
        return df
    if verbose:
        print_boolean_missing_summary(df, boolean_columns)
        print_search_conducted_relatedness(df, boolean_columns)
        print("df.shape before filling Search Conducted:", df.shape)
        print("Search Conducted, before fill (dropna=False):")
        print(df["Search Conducted"].value_counts(dropna=False))

    known = df.dropna(subset=["Search Conducted"])
    group_cols = [c for c in SEARCH_CONDUCTED_GROUP_COLUMNS if c in df]
    if group_cols:
        group_mode = known.groupby(group_cols, observed=True)[
            "Search Conducted"
        ].agg(lambda values: values.mode().iloc[0] if not values.mode(
        ).empty else "No")
        missing = df["Search Conducted"].isna()
        looked_up = df.loc[missing, group_cols].apply(
            lambda row: group_mode.get(tuple(row), "No"), axis=1
        )
        df.loc[missing, "Search Conducted"] = looked_up
    df["Search Conducted"] = df["Search Conducted"].fillna("No")

    if verbose:
        print("Search Conducted, after fill (dropna=False):")
        print(df["Search Conducted"].value_counts(dropna=False))
        print("df.shape after filling Search Conducted:", df.shape)
    return df


def clean_yes_no(df, columns):
    """Turn messy Yes/No text into True/False for each listed column."""
    yes_no = {
        "yes": True, "y": True, "true": True,
        "no": False, "n": False, "false": False,
    }
    for col in columns:
        if col in df.columns:
            df[col] = _clean(df[col], upper=False).map(yes_no).fillna(False)
    return df


def clean_dates_times(df, verbose=False):
    """Parse mixed-format dates/times; blank dates outside MIN_VALID_STOP_YEAR..MAX_VALID_YEAR."""
    if "Date Of Stop" in df.columns:
        df["Date Of Stop"] = pd.to_datetime(
            df["Date Of Stop"], errors="coerce", format="mixed"
        )
        floor = pd.Timestamp(year=MIN_VALID_STOP_YEAR, month=1, day=1)
        cutoff = pd.Timestamp(year=MAX_VALID_YEAR, month=12, day=31)
        invalid = (df["Date Of Stop"] < floor) | (df["Date Of Stop"] > cutoff)
        if verbose:
            print(
                f"Date Of Stop: {invalid.sum()} rows outside "
                f"{floor.date()} - {cutoff.date()}, being removed:"
            )
            print(df.loc[invalid, "Date Of Stop"].value_counts())
        df.loc[invalid, "Date Of Stop"] = pd.NaT
    if "Time Of Stop" in df.columns:
        text = df["Time Of Stop"].astype(str)
        df["Time Of Stop"] = pd.to_datetime(
            text, format="%H:%M:%S", errors="coerce"
        ).dt.time
    return df


def clean_coordinates(df, verbose=False):
    """Blank 0 and out-of-area (MD/DC) coordinates as invalid."""
    if verbose:
        print("Latitude/Longitude, before removing invalid values:")
        print(df[["Latitude", "Longitude"]].isna().sum())
    for col in ("Latitude", "Longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] == 0, col] = np.nan
    if "Latitude" in df.columns and "Longitude" in df.columns:
        valid_lat = df["Latitude"].between(38.5, 39.7)
        valid_lon = df["Longitude"].between(-77.7, -76.5)
        df.loc[~(valid_lat & valid_lon), ["Latitude", "Longitude"]] = np.nan
    if verbose:
        print("Latitude/Longitude, after removing invalid values:")
        print(df[["Latitude", "Longitude"]].isna().sum())
    return df


def clean_year(df, verbose=False):
    """A vehicle year outside a sane range is a data-entry error."""
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        valid = df["Year"].between(MIN_VALID_YEAR, MAX_VALID_YEAR)
        if verbose:
            invalid_values = df.loc[~valid & df["Year"].notna(), "Year"]
            print(
                f"Year: {len(invalid_values)} rows outside "
                f"{MIN_VALID_YEAR}-{MAX_VALID_YEAR}, being removed:"
            )
            print(invalid_values.value_counts().sort_index())
        df.loc[~valid, "Year"] = np.nan
    return df


def standardize_text(df, columns):
    """Trim/uppercase text columns; blanks become real missing values."""
    for col in columns:
        if col in df.columns:
            df[col] = _clean(df[col]).replace({"NAN": np.nan, "": np.nan})
    return df


def _closest_make(value):
    """Return a confident Make correction (unique prefix or close spelling match), else None."""
    if value in CANONICAL_MAKES:
        return None
    prefix_matches = [
        make for make in CANONICAL_MAKES
        if make.startswith(value) and len(value) >= 4
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    if len(prefix_matches) > 1:
        return None
    close = difflib.get_close_matches(
        value, CANONICAL_MAKES, n=1, cutoff=0.82
    )
    return close[0] if close else None


def clean_placeholder_values(df):
    """Blank placeholder values in Make/Model/Driver City/Article, and a bare year in Make."""
    for col in PLACEHOLDER_COLUMNS:
        if col in df.columns:
            values = df[col].astype(str).str.strip().str.upper()
            df.loc[values.isin(PLACEHOLDER_VALUES), col] = np.nan
    if "Make" in df.columns:
        make_str = df["Make"].astype(str).str.strip()
        looks_like_year = make_str.str.match(r"^(19|20)\d{2}$", na=False)
        df.loc[looks_like_year, "Make"] = np.nan
    return df


def standardize_model(df):
    """Fix Model typos via MODEL_CORRECTIONS, scoped by each row's Make."""
    if "Model" not in df.columns or "Make" not in df.columns:
        return df
    for make, corrections in MODEL_CORRECTIONS.items():
        rows = df["Make"] == make
        df.loc[rows, "Model"] = df.loc[rows, "Model"].replace(
            corrections
        )
    return df


def standardize_make(df):
    """Fix car-brand typos/abbreviations against CANONICAL_MAKES."""
    if "Make" not in df.columns:
        return df
    df["Make"] = _clean(df["Make"])
    # Strip a "VAL<year>" system-code suffix glued onto the brand (e.g. "TOYOVAL2011" -> "TOYO").
    df["Make"] = df["Make"].str.replace(
        r"VAL(19|20)\d{2}$", "", regex=True
    )
    # Strip trailing punctuation junk (e.g. "BUICK`", "CHEV.") before matching.
    df["Make"] = df["Make"].str.replace(
        r"[.`,;\\]+$", "", regex=True
    ).str.strip()
    df["Make"] = df["Make"].replace("", np.nan)
    corrections = dict(MAKE_NICKNAMES)
    for value in df["Make"].dropna().unique():
        if value not in corrections:
            match = _closest_make(value)
            if match:
                corrections[value] = match
    df["Make"] = df["Make"].replace(corrections)
    return df


def standardize_gender(df):
    """Keep M/F; map anything else to "UNKNOWN"."""
    if "Gender" in df.columns:
        is_mf = df["Gender"].isin(["M", "F"])
        df["Gender"] = df["Gender"].where(is_mf, "UNKNOWN")
    return df


def clean_state_codes(df):
    """Treat "XX"/"US" as missing across state columns; keep real foreign codes."""
    for col in STATE_COLUMNS:
        if col in df.columns:
            df.loc[df[col].isin(INVALID_STATE_CODES), col] = np.nan
    return df


def standardize_location(df):
    """Normalize intersection separators (@ / AT AND &) and spacing to " @ "."""
    if "Location" in df.columns:
        loc = df["Location"].str.replace(r"\s*/\s*", " @ ", regex=True)
        loc = loc.str.replace(r"\s(AT|AND)\s", " @ ", regex=True)
        loc = loc.str.replace(r"\s&\s", " @ ", regex=True)
        df["Location"] = loc.str.replace(r"\s*@\s*", " @ ", regex=True)
    return df


def extract_road_names(df):
    """Add Location Road 1/2 as additive columns (Road 2 only for a real intersection)."""
    if "Location" not in df.columns:
        return df
    loc = df["Location"]
    has_intersection = loc.str.contains(" @ ", na=False, regex=False)
    split = loc.str.split(" @ ", n=1, expand=True)
    road1 = pd.Series(np.nan, index=df.index, dtype=object)
    road2 = pd.Series(np.nan, index=df.index, dtype=object)
    road1.loc[has_intersection] = split.loc[has_intersection, 0]
    road2.loc[has_intersection] = split.loc[has_intersection, 1]
    no_intersection = ~has_intersection & loc.notna()
    looks_like_address = loc.str.match(r"^\d+\s", na=False)
    contaminated = loc.str.contains(r",|\d{5}$", regex=True, na=False)
    known_cities = "|".join(sorted(set(DRIVER_CITY_MAP.values())))
    city_suffix = loc.str.contains(
        rf"\s(?:{known_cities})\s(?:MD|DC|VA)$", regex=True, na=False
    )
    is_clean_address = no_intersection & looks_like_address
    is_clean_address = is_clean_address & ~contaminated & ~city_suffix
    stripped = loc.str.replace(r"^\d+\s*(BLK\s+)?", "", regex=True)
    road1.loc[is_clean_address] = stripped.loc[is_clean_address]
    df["Location Road 1"] = road1
    df["Location Road 2"] = road2
    return df


def split_code_columns(df):
    """Split VehicleType and Arrest Type into Code + Category/Description (original kept)."""
    for source_col, (code_col, desc_col) in CODE_SPLIT_COLUMNS.items():
        if source_col not in df.columns:
            continue
        split = df[source_col].str.split(" - ", n=1, expand=True)
        df[code_col] = split[0]
        df[desc_col] = split[1]
    return df


def standardize_color(df):
    """Fix the two Color values abbreviating DARK/LIGHT."""
    if "Color" in df.columns:
        df["Color"] = df["Color"].replace(COLOR_MAP)
    return df


# Abbreviated directional/honorific city prefixes normalized to the full word.
DRIVER_CITY_PREFIXES = {
    "MT ": "MOUNT ", "N ": "NORTH ", "S ": "SOUTH ", "E ": "EAST ",
    "W ": "WEST ", "ST ": "SAINT ", "FT ": "FORT ",
}


def clean_driver_city(df):
    """Fix city typos, strip junk/prefixes, recover a real city from digit-noise values, else blank."""
    if "Driver City" not in df.columns:
        return df
    df["Driver City"] = df["Driver City"].replace(DRIVER_CITY_MAP)
    df["Driver City"] = df["Driver City"].str.replace(
        r"^[^A-Z0-9]+", "", regex=True
    )
    for abbr, full in DRIVER_CITY_PREFIXES.items():
        has_prefix = df["Driver City"].str.startswith(abbr, na=False)
        rest = df["Driver City"].str[len(abbr):]
        df.loc[has_prefix, "Driver City"] = full + rest.loc[has_prefix]

    has_digit = df["Driver City"].str.contains(r"\d", regex=True, na=False)
    counts = df.loc[~has_digit, "Driver City"].value_counts()
    known_cities = set(counts[counts >= 5].index)
    recovery_patterns = [
        r"\d",  # strip every digit
        r"^APT\s*\d+\s*",  # strip a leading "APT ###"
        r"^\d+\s*",  # strip a leading house number
        r"\s+(MD|VA|DC)\s+\d{5}$",  # strip a trailing "MD 20906"
    ]
    for value in df.loc[has_digit, "Driver City"].unique():
        for pattern in recovery_patterns:
            candidate = re.sub(pattern, "", value).strip()
            candidate = re.sub(r"\s+", " ", candidate)
            if candidate in known_cities:
                df.loc[df["Driver City"] == value, "Driver City"] = (
                    candidate
                )
                break

    has_digit = df["Driver City"].str.contains(r"\d", regex=True, na=False)
    df.loc[has_digit, "Driver City"] = np.nan
    return df


def clean_legal_codes(df):
    """Fix a stray-space typo, then blank codes missing the article-dash-section shape."""
    for col in LEGAL_CODE_COLUMNS:
        if col not in df.columns:
            continue
        df[col] = df[col].str.replace(r"(\d)\s+(\d)", r"\1\2", regex=True)
        valid_format = df[col].str.match(r"^\d+-\d", na=True)
        df.loc[~valid_format, col] = np.nan
    return df


def fill_article(df):
    """Fill missing Article from a Charge-based lookup, then its dominant value."""
    if "Article" not in df.columns:
        return df
    if "Charge" in df.columns:
        charge_to_article = df.dropna(subset=["Article"]).groupby(
            "Charge"
        )["Article"].agg(lambda values: values.mode().iloc[0])
        looked_up = df["Charge"].map(charge_to_article)
        df["Article"] = df["Article"].fillna(looked_up)
    mode = df["Article"].mode()
    if not mode.empty:
        df["Article"] = df["Article"].fillna(mode.iloc[0])
    return df


def fill_search_not_applicable(df):
    """Fill Search-detail blanks with "NOT APPLICABLE"/"NA" only when no search happened."""
    if "Search Conducted" not in df.columns:
        return df
    no_search = ~df["Search Conducted"]
    for col in SEARCH_NOT_APPLICABLE_COLUMNS:
        if col in df.columns:
            df.loc[no_search & df[col].isna(), col] = "NOT APPLICABLE"
    if SEARCH_NA_COLUMN in df.columns:
        blank = df[SEARCH_NA_COLUMN].isna()
        df.loc[no_search & blank, SEARCH_NA_COLUMN] = "NA"
    return df


def _categorize_violation(text):
    """Return the first matching violation-category keyword group, or "OTHER"."""
    if pd.isna(text):
        return np.nan
    for category, keywords in VIOLATION_CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return category
    return "OTHER"


def engineer_features(df):
    """Add Time Of Day, Day/Month, Accident Severity Score and Violation Category."""
    if "Time Of Stop" in df.columns:
        text = df["Time Of Stop"].astype(str)
        hour = pd.to_datetime(text, format="%H:%M:%S", errors="coerce")
        hour = hour.dt.hour
        bins = [-1, 5, 11, 16, 20, 24]
        labels = ["Late Night", "Morning", "Afternoon", "Evening", "Night"]
        df["Time Of Day"] = pd.cut(hour, bins, labels=labels)
    if "Date Of Stop" in df.columns:
        df["Day Of Week"] = df["Date Of Stop"].dt.day_name()
        df["Month"] = df["Date Of Stop"].dt.month_name()
    flags = ["Fatal", "Personal Injury", "Property Damage", "Accident"]
    severity = [c for c in flags if c in df.columns]
    if severity:
        df["Accident Severity Score"] = df[severity].sum(axis=1)
    if "Description" in df.columns:
        df["Violation Category"] = df["Description"].apply(
            _categorize_violation
        )
    return df


def optimize_dtypes(df):
    """Shrink memory: low-cardinality text -> category, numbers downcast."""
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        if df[col].nunique() / max(len(df), 1) < 0.5:
            df[col] = df[col].astype("category")
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")
    return df


def clean_all(input_path, output_path, verbose=False):
    """Run every cleaning step in order and save the result (verbose=True prints a raw-data look)."""
    df = load_data(input_path)
    if verbose:
        print_dtypes_check(df)
        describe_raw_data(df)
    df = df.drop_duplicates().reset_index(drop=True)
    df = df.drop(columns=REDUNDANT_COLUMNS, errors="ignore")
    # Handle all boolean columns together before text handling begins.
    boolean_columns = detect_boolean_columns(df)
    df = fill_search_conducted_by_group(df, boolean_columns, verbose=verbose)
    df = clean_yes_no(df, boolean_columns)
    text_columns = detect_text_columns(df, boolean_columns)
    df = clean_dates_times(df, verbose=verbose)
    df = clean_coordinates(df, verbose=verbose)
    df = clean_year(df, verbose=verbose)
    df = standardize_text(df, text_columns)
    df = clean_placeholder_values(df)
    df = standardize_make(df)
    df = standardize_model(df)
    df = standardize_gender(df)
    df = clean_state_codes(df)
    df = standardize_location(df)
    df = extract_road_names(df)
    df = split_code_columns(df)
    df = standardize_color(df)
    df = clean_driver_city(df)
    df = clean_legal_codes(df)
    df = fill_article(df)
    df = fill_search_not_applicable(df)
    df = engineer_features(df)
    df = optimize_dtypes(df)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    clean_all(
        "Traffic_Violations.csv", "traffic_violations_clean.csv",
        verbose=True,
    )
