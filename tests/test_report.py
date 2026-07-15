import yaml
from src.bloomberg import load_fixture
from src.report import build_report

EXPECTED = (
    "Good morning!\n"
    "* Macro\n"
    "{SK} KR: Employment Data\n"
    "{JN} JP: Core Machine Orders\n"
    "{CH} CH: GDP / Retail Sales / Industrial Prod\n"
    "* Market Holiday: None\n"
    "* Non-Standard Settlement Days: {SK} KR: 20/7\n"
    "* Markets\n"
    "{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps\n"
    "1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps\n"
    "* ETFs Overnight\n"
    "PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps\n"
    "DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps\n"
    "* Market Overview\n"
)

def test_dry_run_matches_template_byte_for_byte():
    cfg = yaml.safe_load(open("config.yaml"))
    data = load_fixture()
    assert build_report(data, cfg) == EXPECTED

def test_section_failure_degrades_to_placeholder():
    cfg = yaml.safe_load(open("config.yaml"))
    data = load_fixture()
    del data["indices"]          # markets.render will still run (uses .get) -> N/A values, not crash
    data["commodities"] = None   # force a real exception inside the markets section
    out = build_report(data, cfg)
    assert "* Markets\nN/A" in out   # placeholder substituted, report still whole
    assert out.endswith("* Market Overview\n")
