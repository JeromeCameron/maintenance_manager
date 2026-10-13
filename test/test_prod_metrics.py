import pytest

from utils.prod_metrics import availability, mtbf, mttr


class TestAvailability:
    def test_unplanned_only(self):
        assert availability(200, 10) == pytest.approx(95.0)

    def test_planned_comes_out_of_scheduled(self):
        # 200 scheduled, 40 planned PM, 10 breakdown -> 150 / 160
        assert availability(200, 10, planned_hours=40) == pytest.approx(93.75)

    def test_planned_only_is_fully_available(self):
        assert availability(200, 0, planned_hours=40) == pytest.approx(100.0)

    def test_whole_period_planned_shutdown(self):
        assert availability(200, 0, planned_hours=200) == 100

    def test_no_scheduled_hours(self):
        assert availability(0, 0) == 0

    def test_never_negative(self):
        assert availability(100, 150) == 0


class TestMtbf:
    def test_unplanned_only(self):
        assert mtbf(200, 10, 2) == pytest.approx(95.0)

    def test_planned_comes_out_of_scheduled(self):
        assert mtbf(200, 10, 2, planned_hours=40) == pytest.approx(75.0)

    def test_no_failures(self):
        assert mtbf(200, 0, 0, planned_hours=40) == 0


class TestMttr:
    def test_unchanged_by_planned(self):
        assert mttr(10, 2) == pytest.approx(5.0)
