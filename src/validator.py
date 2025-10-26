import sys, json, os
from datetime import datetime

def parse_iso(s: str):
    """
    :param s: datetime in str format
    :return: datetime formated obj

    parse an ISO 8601 timestamp string
    "Z" means “UTC time zone” , if string ends with 'Z' then,
    s[:-1] removes the last character, then we add "+00:00" (which is another way to say UTC)
    Main aim of function converting str formated to datetime format which used for compare.
    """
    if s is None:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)

def overlaps(a_start, a_end, b_start, b_end):
    """
    :param a_start: datetime.datetime format
    :param a_end: datetime.datetime format
    :param b_start: datetime.datetime format
    :param b_end: datetime.datetime format
    :return: boolean True/False

    It returns True if:
        The first starts before the second ends, and
        The second starts before the first ends.
    Otherwise, returns False.
    """
    # return True if time ranges [a_start, a_end) and [b_start, b_end) overlap strictly
    return (a_start < b_end) and (b_start < a_end)

def load(path):
    """
    :param path: json file path.
    :return: json data converted to python dict.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate(plan):
    """
    :param plan: All the info in dict format
    :return:
    """
    errors = []

    # build lookups
    orders = plan.get("inputs", {}).get("product_orders", [])
    equipment = plan.get("inputs", {}).get("equipment", [])
    downtimes = plan.get("inputs", {}).get("constraints", {}).get("downtimes", [])
    holidays = plan.get("inputs", {}).get("constraints", {}).get("holidays", [])
    batches = plan.get("outputs", {}).get("production_batches", [])

    eq_by_id = {e["equipment_id"]: e for e in equipment}

    # Check: start_time < end_time for batches and valid date format
    for b in batches:
        try:
            s = parse_iso(b["start_time"]); e = parse_iso(b["end_time"])
            if s is None or e is None:
                errors.append(f"ERROR: Batch {b.get('batch_id')} has missing start_time or end_time.")
                continue
            if s >= e:
                errors.append(f"ERROR: Batch {b.get('batch_id')} start_time ({b.get('start_time')}) >= end_time ({b.get('end_time')}).")
        except Exception as ex:
            errors.append(f"ERROR: Batch {b.get('batch_id')} has invalid datetime format: {ex}")

    # Check 1: Quantity conservation
    # collect Order and Batch product_code and quantity_kg and see it match or Not
    from collections import defaultdict
    orders_sum = defaultdict(float)
    for o in orders:
        orders_sum[o["product_code"]] += float(o["quantity_kg"])
    batches_sum = defaultdict(float)
    for b in batches:
        batches_sum[b["product_code"]] += float(b["quantity_kg"])

    # compare keys and values
    all_products = set(orders_sum.keys()) | set(batches_sum.keys())
    for p in sorted(all_products):
        o_qty = round(orders_sum.get(p, 0.0), 9)
        b_qty = round(batches_sum.get(p, 0.0), 9)
        if o_qty != b_qty: # confirming 1st Rule in Quantity Conservation
            errors.append(f"ERROR: Quantity mismatch for product {p}: orders={o_qty} kg vs batches={b_qty} kg.")
            # instead for assert here only I am trying to collect all error's in json file
            # if PROD code not available in both batch and order then also it's handled here.

    # Check 2: Equipment sizing and compatibility
    print(f'we have {len(batches)} Batches currently')
    for b in batches:
        bid = b.get("batch_id")
        eq_id = b.get("equipment_id")
        qty = float(b.get("quantity_kg", 0.0))
        if eq_id not in eq_by_id: # check is assigned equipment is correct or not.
            errors.append(f"ERROR: Batch {bid} assigned to unknown equipment {eq_id}.")
            continue
        eq = eq_by_id[eq_id]
        min_c = float(eq.get("min_capacity_kg", 0.0))
        max_c = float(eq.get("max_capacity_kg", 1e18))
        # compatibility
        allowed_products = eq.get("product_codes", [])
        if b.get("product_code") not in allowed_products:
            errors.append(f"ERROR: Batch {bid} product {b.get('product_code')} not supported by equipment {eq_id} (allowed: {allowed_products}).")
        if qty < min_c:
            errors.append(f"ERROR: Batch {bid} ({qty} kg) is below min capacity ({min_c} kg) for {eq_id}.")
        if qty > max_c:
            errors.append(f"ERROR: Batch {bid} ({qty} kg) is above max capacity ({max_c} kg) for {eq_id}.")

    # Check 3: Downtimes & Holidays
    # parse downtimes and holidays to ranges

    dt_by_eq = {} # downtime id , Start and End Time
    for d in downtimes:
        eqid = d.get("equipment_id")
        s = parse_iso(d.get("start_time")); e = parse_iso(d.get("end_time"))
        dt_by_eq.setdefault(eqid, []).append((s,e,d.get("downtime_id")))
    hols = [] # Holiday name , Start and End Time
    for h in holidays:
        s = parse_iso(h.get("start_time")); e = parse_iso(h.get("end_time"))
        hols.append((s,e,h.get("holiday_name")))

    for b in batches:
        bid = b.get("batch_id")
        s = parse_iso(b.get("start_time")); e = parse_iso(b.get("end_time"))
        if s is None or e is None:
            continue
        # Once Batch Start and end time we got , check if it's overlaps with Holiday times or downtimes
        # equipment downtimes
        for (ds,de,did) in dt_by_eq.get(b.get("equipment_id"), []):
            if overlaps(s,e,ds,de):
                errors.append(f"ERROR: Batch {bid} ({s.isoformat()} - {e.isoformat()}) overlaps downtime {did} on {b.get('equipment_id')} ({ds.isoformat()} - {de.isoformat()}).")
        # holidays
        for (hs,he,h_name) in hols:
            if overlaps(s,e,hs,he):
                errors.append(f"ERROR: Batch {bid} ({s.isoformat()} - {e.isoformat()}) overlaps holiday '{h_name}' ({hs.isoformat()} - {he.isoformat()}).")

    # Check 4: No equipment overlaps
    batches_by_eq = {}
    # map eq_name to all batches using this eq_name. in 2 batch may use same eq.
    for b in batches:
        batches_by_eq.setdefault(b.get("equipment_id"), []).append(b)
    # equipment_id and Batch List means Batch data
    for eqid, blist in batches_by_eq.items():
        # sort by start_time
        def _start(bs):
            return parse_iso(bs.get("start_time"))
        blist_sorted = sorted(blist, key=_start)
        for i in range(len(blist_sorted)-1):
            cur = blist_sorted[i]; nxt = blist_sorted[i+1]
            cur_end = parse_iso(cur.get("end_time")); nxt_start = parse_iso(nxt.get("start_time"))
            if cur_end is None or nxt_start is None:
                continue
            if cur_end > nxt_start:
                errors.append(f"ERROR: Equipment {eqid} has overlapping batches: {cur.get('batch_id')} ends at {cur_end.isoformat()} > {nxt.get('batch_id')} starts at {nxt_start.isoformat()}.")

    return errors

def optima(argv):
    if len(argv) < 2:
        print("Usage: validator.py path/to/schedule_plan.json")
        return 2
    path = argv[1]
    try:
        plan = load(path)
    except Exception as ex:
        print(f"Failed to load JSON: {ex}")
        return 2
    errors = validate(plan)
    if errors:
        print(f"VALIDATION FAILED: Found the following issues: {os.path.basename(path)}")
        for e in errors:
            print(e)
        return 1
    else:
        print(f"VALIDATION PASSED with {os.path.basename(path)}: No issues found.")
        return 0

if __name__ == '__main__':
    rv = optima(sys.argv)
    sys.exit(rv)
