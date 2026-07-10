"""Tests del clasificador de correos. Correr con: python3 -m pytest -q
(o simplemente: python3 tests/test_clasificador.py)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from correos.clasificador import clasificar_correo


def test_coach_edu_con_firma():
    r = clasificar_correo(
        "Jane Doe <jdoe@athletics.stanford.edu>",
        "Interested in your profile",
        "We are NCAA Division I. Best, Jane Doe, Head Women's Swimming Coach.",
    )
    assert r.categoria == "COACH"
    assert r.universidad == "Stanford"
    assert r.division == "NCAA D1"
    assert r.nombre_coach == "Jane Doe"


def test_plataforma_ncsa():
    r = clasificar_correo("recruiting@ncsasports.org", "A coach viewed your profile", "...")
    assert r.categoria == "PLATAFORMA"
    assert r.plataforma == "NCSA"


def test_universidad_admisiones():
    r = clasificar_correo(
        "admissions@utexas.edu", "Your application",
        "Info about scholarship for student-athletes.",
    )
    assert r.categoria == "UNIVERSIDAD"
    assert r.universidad == "Utexas"


def test_division_ii_y_juco():
    r2 = clasificar_correo("coach@queens.edu", "D2", "NCAA Division II swim team, questionnaire.")
    assert r2.division == "NCAA D2"
    rj = clasificar_correo("info@indianriver.edu", "JUCO", "NJCAA program, prospect, time standard.")
    assert rj.division == "NJCAA (JUCO)"


def test_division_i_sin_ncaa():
    r = clasificar_correo("mrivera@go.utexas.edu", "visit", "We are a Division I swim program.")
    assert r.division == "NCAA D1"


def test_otro_no_relacionado():
    r = clasificar_correo("promos@tienda.com", "Ofertas", "Descuentos de verano")
    assert r.categoria == "OTRO"


def test_no_confunde_the_head_con_nombre():
    r = clasificar_correo(
        "x@athletics.mit.edu", "hi",
        "I'm the Head Swimming Coach and we recruit swimmers.",
    )
    assert r.categoria == "COACH"
    assert r.nombre_coach is None  # 'the Head' NO es un nombre válido


def _run():
    fns = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")


if __name__ == "__main__":
    _run()
