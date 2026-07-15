from src.formatting import fmt_bps_1dp, fmt_bps_int

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
