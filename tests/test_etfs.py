import yaml
from src.bloomberg import load_fixture
from src.sections.etfs import compute_bps, render

def test_compute_bps():
    # px 10.53 on nav 10.00 -> +530 ... use a clean case
    assert round(compute_bps(101.0, 100.0), 1) == 100.0
    assert compute_bps(None, 100.0) is None
    assert compute_bps(100.0, 0) is None

def test_render_from_fixture():
    cfg = yaml.safe_load(open("config.yaml"))
    d = load_fixture()
    out = render(d, cfg)
    assert out == (
        "PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps\n"
        "DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps"
    )

def test_render_from_live_shape():
    cfg = yaml.safe_load(open("config.yaml"))
    # minimal live-shaped data: one premium, one discount
    cfg = {"flags": cfg["flags"], "etfs": [
        {"label": "KR", "ticker": "EWY US Equity"},
        {"label": "HK", "ticker": "EWH US Equity"},
    ]}
    d = {"etf_prices": {
        "KR": {"px": 100.53, "nav": 100.0},   # +53 bps
        "HK": {"px": 99.59, "nav": 100.0},     # -41 bps
    }}
    out = render(d, cfg)
    assert out == "PREMIUM: KR +53bps\nDISCOUNT: HK -41bps"
