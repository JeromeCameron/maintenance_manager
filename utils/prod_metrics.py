# Planned downtime is taken out of scheduled hours before availability and MTBF
# are calculated: a planned shutdown is neither a failure nor available time.
# downtime_hours and num_failures are unplanned only.


def mtbf(scheduled_hours, downtime_hours, num_failures, planned_hours=0) -> float:
    if num_failures == 0:
        return 0
    return (scheduled_hours - planned_hours - downtime_hours) / num_failures


def mttr(downtime_hours, num_failures) -> float:
    if num_failures == 0:
        return 0
    return downtime_hours / num_failures


def availability(scheduled_hours, downtime_hours, planned_hours=0) -> float:
    if scheduled_hours == 0:
        return 0
    net_scheduled = scheduled_hours - planned_hours
    if net_scheduled <= 0:
        return 100  # whole period was a planned shutdown; nothing lost to failures
    return max(0, (net_scheduled - downtime_hours) / net_scheduled) * 100


def cost_per_operating_hour(repair_cost, scheduled_hours, downtime_hours) -> float:
    uptime = scheduled_hours - downtime_hours

    if uptime <= 0:
        return 0  # or None / float('inf') depending on use

    return repair_cost / uptime


def cost_per_scheduled_hour(repair_cost, scheduled_hours):
    if scheduled_hours == 0:
        return 0
    return repair_cost / scheduled_hours


def cost_per_downtime_hour(repair_cost, downtime_hours):
    if downtime_hours == 0:
        return 0
    return repair_cost / downtime_hours


def calculate_all_kpis(scheduled_hours, downtime_hours, num_failures, repair_cost, planned_hours=0):
    return {
        "availability_%": round(availability(scheduled_hours, downtime_hours, planned_hours), 2),
        "mttr_hours": round(mttr(downtime_hours, num_failures), 2),
        "mtbf_hours": round(mtbf(scheduled_hours, downtime_hours, num_failures, planned_hours), 2),
        "cost_per_operating_hour": round(
            cost_per_operating_hour(repair_cost, scheduled_hours, downtime_hours), 2
        ),
        "cost_per_scheduled_hour": round(
            cost_per_scheduled_hour(repair_cost, scheduled_hours), 2
        ),
        "cost_per_downtime_hour": round(
            cost_per_downtime_hour(repair_cost, downtime_hours), 2
        ),
    }
