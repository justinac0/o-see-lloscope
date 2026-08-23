import numpy as np
from osee.actions.actions import autoFunc, measureFunc, captureFunc, divScaleFunc, couplingFunc


class FakeScope:
    """Minimal stand-in for a scope: records writes, answers queries, feeds bytes."""
    def __init__(self, answers=None, byte_chunks=None):
        self.written = []
        self.answers = answers or {}
        self.byte_chunks = list(byte_chunks or [])

    def write(self, cmd):
        self.written.append(cmd)

    def query(self, cmd):
        return self.answers.get(cmd, "0")

    def read_bytes(self, n):
        return self.byte_chunks.pop(0)


def test_auto_sends_autoscale():
    scope = FakeScope()
    autoFunc(scope, [])
    assert ":AUToscale" in scope.written


def test_measure_sends_autoscale_and_reads_values(capsys):
    scope = FakeScope(answers={
        ":MEASure:ITEM? VPP,CHANnel1": "3.3",
        ":MEASure:ITEM? FREQuency,CHANnel1": "1000",
        ":MEASure:ITEM? VAVG,CHANnel1": "1.65",
    })
    measureFunc(scope, [])
    assert ":AUToscale" in scope.written
    out = capsys.readouterr().out
    assert "Vpp = 3.300 V" in out
    assert "f = 1000.0 Hz" in out
    assert "Vavg = 1.650 V" in out


def test_divscale_sends_channel_and_timebase_scale(capsys):
    scope = FakeScope()
    divScaleFunc(scope, ["1", "0.5", "0.001"])

    assert ":CHANnel1:SCALe 0.5" in scope.written
    assert ":TIMebase:SCALe 0.001" in scope.written
    assert "CH1: 0.5 V/div, 0.001 s/div" in capsys.readouterr().out


def test_coupling_sends_valid_mode(capsys):
    scope = FakeScope()
    couplingFunc(scope, ["1", "AC"])

    assert ":CHANnel1:COUPling AC" in scope.written
    assert "CH1: coupling set to AC" in capsys.readouterr().out


def test_coupling_lowercase_mode_is_normalized(capsys):
    scope = FakeScope()
    couplingFunc(scope, ["2", "dc"])

    assert ":CHANnel2:COUPling DC" in scope.written


def test_coupling_rejects_invalid_mode(capsys):
    scope = FakeScope()
    couplingFunc(scope, ["1", "XYZ"])

    assert scope.written == []
    assert "invalid coupling mode" in capsys.readouterr().out


def test_capture_reads_positioning_scaling_factors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    scope = FakeScope(
        answers={
            ":WAVeform:XINCrement?": "1e-6",
            ":WAVeform:YINCrement?": "0.01",
            ":WAVeform:YORigin?": "0",
            ":WAVeform:YREFerence?": "0",
        },
        byte_chunks=[b"#3", b"005", bytes([10, 20, 30, 40, 50]) + b"\n"],
    )

    captureFunc(scope, ["1"])

    assert ":WAVeform:SOURce CHANnel1" in scope.written
    assert (tmp_path / "capture.png").exists()

    data = np.loadtxt(tmp_path / "capture.csv", delimiter=",", skiprows=1)
    assert data[0, 1] == 0.10
