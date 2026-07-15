from src.formatting import (
    fmt_bps_1dp, fmt_bps_int,
    build_macro, build_holiday, build_settlement,
    build_markets, build_commodities, build_etfs, N_A,
)

FLAGS = {"KR": "{SK}", "JP": "{JN}", "CH": "{CH}", "AU": "{AU}", "HK": "{HK}"}

def test_fmt_bps_1dp_drops_trailing_zero():
    assert fmt_bps_1dp(0.91) == "+91"

def test_fmt_bps_1dp_keeps_decimal():
    assert fmt_bps_1dp(0.097) == "+9.7"

def test_fmt_bps_1dp_negative():
    assert fmt_bps_1dp(-2.024) == "-202.4"

def test_fmt_bps_1dp_zero_is_positive_sign():
    assert fmt_bps_1dp(0.0) == "+0"

def test_fmt_bps_int_positive():
    assert fmt_bps_int(53) == "+53"

def test_fmt_bps_int_negative():
    assert fmt_bps_int(-12) == "-12"

def test_fmt_bps_int_rounds():
    assert fmt_bps_int(4.6) == "+5"

def test_fmt_bps_1dp_tiny_negative_is_positive_zero():
    assert fmt_bps_1dp(-0.00001) == "+0"


def test_build_macro():
    rows = [
        {"country": "KR", "event": "Employment Data"},
        {"country": "JP", "event": "Core Machine Orders"},
        {"country": "CH", "event": "GDP / Retail Sales / Industrial Prod"},
    ]
    assert build_macro(rows, FLAGS) == (
        "{SK} KR: Employment Data\n"
        "{JN} JP: Core Machine Orders\n"
        "{CH} CH: GDP / Retail Sales / Industrial Prod"
    )

def test_build_holiday_none():
    assert build_holiday([], FLAGS) == "* Market Holiday: None"

def test_build_holiday_one():
    assert build_holiday([{"country": "HK", "name": "Some Day"}], FLAGS) == \
        "* Market Holiday: {HK} HK: Some Day"

def test_build_settlement_one():
    assert build_settlement([{"country": "KR", "date": "20/7"}], FLAGS) == \
        "* Non-Standard Settlement Days: {SK} KR: 20/7"

def test_build_settlement_none():
    assert build_settlement([], FLAGS) == "* Non-Standard Settlement Days: None"

def test_build_markets():
    indices = {"AU": 0.097, "JP": 0.91, "CH": -2.024, "HK": 0.244}
    assert build_markets(indices, FLAGS, ["AU", "JP", "CH", "HK"]) == \
        "{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps"

def test_build_markets_missing_value():
    indices = {"AU": None, "JP": 0.91, "CH": -2.024, "HK": 0.244}
    out = build_markets(indices, FLAGS, ["AU", "JP", "CH", "HK"])
    assert "{AU} AU: N/A" in out

def test_build_commodities():
    comm = {"Brent": 0.794, "Gold": -0.078, "Bitcoin": 0.485}
    assert build_commodities(comm, ["Brent", "Gold", "Bitcoin"]) == \
        "1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps"

def test_build_etfs():
    order = ["KR", "JP", "ID", "MY", "PH", "FXI CHINA", "EEM", "HK", "TW", "TH", "AU"]
    etf_bps = {"KR": 53, "JP": 34, "ID": 45, "MY": 24, "PH": 5,
               "FXI CHINA": -12, "EEM": -1, "HK": -41, "TW": -27, "TH": -6, "AU": -9}
    prem, disc = build_etfs(etf_bps, order)
    assert prem == "PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps"
    assert disc == "DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps"
