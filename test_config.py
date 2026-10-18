import config_logic as c

base = c.effective_config([])
print(base)
assert base == {"port": 8667, "workers": 13, "debug": True, "log_level": "info", "api_key": "****"}
assert type(base["port"]) is int and type(base["debug"]) is bool

r = c.effective_config(["port=9000", "debug=false", "workers=2", "log_level=DEBUG", "api_key=hunter2", "extra=x=y"])
print(r)
assert r["port"] == 9000 and r["workers"] == 2 and r["debug"] is False and r["log_level"] == "DEBUG"
assert r["api_key"] == "****" and r["extra"] == "x=y"
for v, exp in [("TRUE", True), ("1", True), ("Yes", True), ("ON", True), ("off", False), ("0", False), ("no", False), ("maybe", False)]:
    assert c.effective_config([f"debug={v}"])["debug"] is exp, v
assert c.effective_config(["port=1", "port=2"])["port"] == 2          # later set wins

# .env layer incl. NUM_WORKERS alias; OS layer still beats .env
de = c.parse_dotenv("# c\nNUM_WORKERS=7\nPORT=1234\nexport LOG_LEVEL='warn'\nDEBUG=yes\n")
assert de == {"workers": "7", "port": "1234", "log_level": "warn", "debug": "yes"}, de
r = c.effective_config([], dotenv_layer=de, os_layer={})
assert r["workers"] == 7 and r["port"] == 1234 and r["log_level"] == "warn" and r["debug"] is True
r = c.effective_config([], dotenv_layer=de)          # real OS layer wins over .env
assert r["workers"] == 13 and r["port"] == 8667
# secrets never leak, even if api_key comes from every layer
assert c.effective_config(["api_key=zzz"])["api_key"] == "****"
for bad in (["noequals"], ["=x"], ["port=abc"]):
    try: c.effective_config(bad); raise SystemExit(f"should fail: {bad}")
    except ValueError: pass
print("ALL OK")
