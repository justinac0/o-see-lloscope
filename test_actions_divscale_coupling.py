from actions import divScaleFunc, couplingFunc


class FakeScope:
    """Minimal stand-in for a scope: just records what was written."""
    def __init__(self):
        self.written = []

    def write(self, cmd):
        self.written.append(cmd)


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
