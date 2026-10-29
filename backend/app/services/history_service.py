"""
Report numbers for a user's scan history (weekly / monthly / 90 days).
Pure logic: no database, so it is easy to test.
"""

from datetime import timedelta, timezone

GRADES = ["A", "B", "C", "D"]
TOP_N = 6


def split_cautions(text):
    return [c for c in (text or "").split(",") if c]


def to_utc(moment):
    """SQLite gives back naive datetimes, PostgreSQL aware ones. Treat both as UTC."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _average(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None


def _product_key(entry):
    if entry.get("product_id"):
        return f"p{entry['product_id']}"
    if entry.get("barcode"):
        return f"b{entry['barcode']}"
    return "n" + (entry.get("product_name") or "").strip().lower()


def _insights(total, avg, change, days, grades, top_cautions):
    if total == 0:
        return []

    notes = []

    healthy = grades["A"] + grades["B"]
    share = round(healthy / total * 100)
    if share >= 50:
        notes.append(f"{share}% of the products you checked were grade A or B.")
    else:
        notes.append(
            f"Only {share}% of the products you checked were grade A or B. "
            "The healthier alternatives on each product page can help.")

    if top_cautions:
        top = top_cautions[0]
        notes.append(
            f"The most common concern was {top['label']} "
            f"(in {top['count']} of {total} products).")

    if change is not None:
        if change >= 3:
            notes.append(
                f"Your average score is {change:.0f} points higher than in the "
                f"previous {days} days.")
        elif change <= -3:
            notes.append(
                f"Your average score is {abs(change):.0f} points lower than in the "
                f"previous {days} days.")
        else:
            notes.append(f"Your average score is about the same as in the previous {days} days.")

    return notes


def summarize(entries, days, now, tz_offset_minutes=0):
    """
    entries: dicts with created_at, score, grade, category, product_name,
             product_id, barcode, cautions (list), calories, sugar, sodium,
             saturated_fat.
    now: aware datetime. tz_offset_minutes: minutes the user's clock is ahead
    of UTC (India = 330), so a "day" matches the user's own day.
    """
    shift = timedelta(minutes=tz_offset_minutes)
    today = (now + shift).date()
    start = today - timedelta(days=days - 1)
    prev_start = start - timedelta(days=days)

    current, previous = [], []
    for entry in entries:
        day = (to_utc(entry["created_at"]) + shift).date()
        if start <= day <= today:
            current.append((day, entry))
        elif prev_start <= day < start:
            previous.append(entry)

    rows = [entry for _, entry in current]
    total = len(rows)

    avg = _average([e["score"] for e in rows])
    prev_avg = _average([e["score"] for e in previous])
    change = round(avg - prev_avg, 1) if avg is not None and prev_avg is not None else None

    grades = {g: 0 for g in GRADES}
    for e in rows:
        if e["grade"] in grades:
            grades[e["grade"]] += 1

    by_day = {}
    for day, e in current:
        by_day.setdefault(day, []).append(e["score"])

    daily = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        scores = by_day.get(day, [])
        daily.append({
            "date": day.isoformat(),
            "count": len(scores),
            "average": _average(scores),
        })

    caution_counts = {}
    for e in rows:
        for label in set(e.get("cautions") or []):
            caution_counts[label] = caution_counts.get(label, 0) + 1
    top_cautions = [
        {"label": label, "count": count}
        for label, count in sorted(caution_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ][:TOP_N]

    by_category = {}
    for e in rows:
        if e.get("category"):
            by_category.setdefault(e["category"], []).append(e["score"])
    categories = [
        {"category": name, "count": len(scores), "average": _average(scores)}
        for name, scores in sorted(by_category.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ][:TOP_N]

    best = max(rows, key=lambda e: e["score"]) if rows else None
    worst = min(rows, key=lambda e: e["score"]) if rows else None

    def card(e):
        return None if e is None else {
            "product_name": e["product_name"], "score": e["score"], "grade": e["grade"]}

    return {
        "days": days,
        "period": {"start": start.isoformat(), "end": today.isoformat()},
        "total": total,
        "unique_products": len({_product_key(e) for e in rows}),
        "average_score": avg,
        "previous": {"total": len(previous), "average_score": prev_avg},
        "change": change,
        "grades": grades,
        "healthy_share": round((grades["A"] + grades["B"]) / total * 100) if total else None,
        "daily": daily,
        "top_cautions": top_cautions,
        "categories": categories,
        "averages": {
            key: _average([e.get(key) for e in rows])
            for key in ("calories", "sugar", "sodium", "saturated_fat")
        },
        "best": card(best),
        "worst": card(worst),
        "insights": _insights(total, avg, change, days, grades, top_cautions),
    }