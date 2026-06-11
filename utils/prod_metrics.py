def mtbf(scheduled_hours, downtime_hours, num_failures) -> float:
    if num_failures == 0:
        return 0
    return (scheduled_hours - downtime_hours) / num_failures


def mttr(downtime_hours, num_failures) -> float:
    if num_failures == 0:
        return 0
    return downtime_hours / num_failures


def availability(scheduled_hours, downtime_hours) -> float:
    if scheduled_hours == 0:
        return 0
    return ((scheduled_hours - downtime_hours) / scheduled_hours) * 100


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


def calculate_all_kpis(scheduled_hours, downtime_hours, num_failures, repair_cost):
    return {
        "availability_%": round(availability(scheduled_hours, downtime_hours), 2),
        "mttr_hours": round(mttr(downtime_hours, num_failures), 2),
        "mtbf_hours": round(mtbf(scheduled_hours, downtime_hours, num_failures), 2)
        if mtbf(scheduled_hours, downtime_hours, num_failures) is not None
        else None,
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
