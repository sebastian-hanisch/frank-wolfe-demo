"""Presets: vollständig, in den Grenzen, und jedes Beispiel zeigt, was sein Hilfetext behauptet."""

import pytest

import fw_constants as C
import fw_evaluation as ev
import fw_presets as P

KEYS = set(P.PRESET_KEYS)


def _params(p):
    return ev.Params(p["net"], p["side"], p["zones"], p["load"], p["mode"], p["method"], p["iterations"], p["seed"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    assert all(C.PRESET_HELP[name].strip() for name in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_values_are_inside_the_bounds_and_on_the_step_grid(name):
    p = C.PRESETS[name]
    assert p["net"] in C.NETS and p["mode"] in C.MODES and p["method"] in C.METHODS and p["iterations"] in C.ITERATIONS
    for key, state_key in P.PRESET_KEYS.items():
        spec = P.SETTING_SPECS[state_key]
        if spec.lo is not None:
            assert spec.lo <= p[key] <= spec.hi, (name, key)
    assert (p["load"] - C.LOAD_MIN) % 5 == 0


def test_setting_specs_have_room_to_move():
    """Ein Regler mit lo == hi würde Streamlit abstürzen lassen."""
    assert all(spec.lo < spec.hi for spec in P.SETTING_SPECS.values() if spec.lo is not None)


def test_presets_use_seeds_outside_the_distribution_set():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def test_defaults_equal_the_first_preset():
    p = C.PRESETS["🏙️ Stadtgitter"]
    assert (p["net"], p["side"], p["zones"], p["load"], p["mode"], p["method"], p["iterations"], p["seed"]) == (
        C.DEFAULT_NET, C.DEFAULT_SIDE, C.DEFAULT_ZONES, C.DEFAULT_LOAD, C.DEFAULT_MODE, C.DEFAULT_METHOD, C.DEFAULT_ITERATIONS, C.DEFAULT_SEED)


def test_fixed_presets_hide_the_random_controls():
    assert {n for n, p in C.PRESETS.items() if p["net"] in C.FIXED_NETS} == {"🛣️ Pigou-Netz"}


def test_the_presets_show_both_good_and_bad_news():
    """Gut: die Verfahren mit Suche und das konjugierte Verfahren erreichen eine kleine Lücke; schlecht: hohe Last (kein 1e-3 in 200 Iterationen), MSA (kein 1e-4) und der feste Schritt (nie unter 1e-2)."""
    res = {n: ev.analyse(_params(p))["result"] for n, p in C.PRESETS.items()}
    assert res["🔗 Konjugiert"].first_below(1e-5) is not None and res["🌙 Niedrige Last"].first_below(1e-4) is not None
    assert res["🚗 Hohe Last"].first_below(1e-3) is None and res["🐢 Nur MSA"].first_below(1e-4) is None
    assert res["🧪 Fester Schritt"].first_below(1e-2) is None and res["🛣️ Pigou-Netz"].iterations == 0
