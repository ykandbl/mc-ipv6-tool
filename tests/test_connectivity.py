from types import SimpleNamespace

import connectivity_test
from connectivity_test import (
    combine_direction_results,
    get_isp_info,
    ping_ipv6,
)


def test_combine_direction_results_covers_all_host_choices():
    assert combine_direction_results(True, True)["code"] == "both"
    assert combine_direction_results(True, False)["code"] == "remote_only"
    assert combine_direction_results(False, True)["code"] == "local_only"
    assert combine_direction_results(False, False)["code"] == "neither"


def test_isp_detection_only_marks_known_chinese_prefixes():
    assert get_isp_info("240e::1") == "中国电信"
    assert get_isp_info("2408::1") == "中国联通"
    assert get_isp_info("2409::1") == "中国移动"
    assert get_isp_info("2a00::1") == "其他或未知运营商"


def test_ping_parses_chinese_average(monkeypatch):
    monkeypatch.setattr(
        connectivity_test.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="往返行程的估计时间(以毫秒为单位):\n    最短 = 10ms，最长 = 20ms，平均 = 15ms",
            stderr="",
        ),
    )
    success, _, latency = ping_ipv6("2409::1", count=1)
    assert success is True
    assert latency == 15


def test_ping_parses_english_average(monkeypatch):
    monkeypatch.setattr(
        connectivity_test.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="Minimum = 8ms, Maximum = 12ms, Average = 10ms",
            stderr="",
        ),
    )
    assert ping_ipv6("2409::1", count=1)[2] == 10
