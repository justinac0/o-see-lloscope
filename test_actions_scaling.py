import numpy as np
from actions import autoFunc, scaleFunc, measureFunc, captureFunc


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


def test_scale_and_measure_send_autoscale_and_read_values(capsys):
    scope = FakeScope(answers={
        ":MEASure:ITEM? VPP,CHANnel1": "3.3",
        ":MEASure:ITEM? FREQuency,CHANnel1": "1000",
        ":MEASure:ITEM? VAVG,CHANnel1": "1.65",
    })
    for func in (scaleFunc, measureFunc):
        scope.written.clear()
        func(scope, [])
        assert ":AUToscale" in scope.written
        out = capsys.readouterr().out
        assert "Vpp = 3.300 V" in out
        assert "f = 1000.0 Hz" in out
        assert "Vavg = 1.650 V" in out


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
