"""Validate GPU booking references, explicit time zones and active-slot conflicts."""
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from validate_results import ROOT, load_json

MEMBERS = {'TV1', 'TV2', 'TV3', 'TV4'}
ACTIVE = {'confirmed', 'running'}
STATUSES = ACTIVE | {'requested', 'completed', 'cancelled'}


def validate_schedule(schedule):
    errors = []
    if not isinstance(schedule, dict) or schedule.get('timezone') != 'Asia/Ho_Chi_Minh':
        return ['Expected an object with timezone Asia/Ho_Chi_Minh']
    if not isinstance(schedule.get('resources'), list) or not isinstance(schedule.get('reservations'), list):
        return ['resources and reservations must be arrays']
    resources = {}
    for resource in schedule['resources']:
        if not isinstance(resource, dict):
            errors.append('Resource must be an object'); continue
        rid = resource.get('resource_id')
        if not isinstance(rid, str) or not rid or rid in resources:
            errors.append('Resource IDs must be nonempty and unique'); continue
        resources[rid] = resource
        if resource.get('type') not in {'local', 'colab'} or type(resource.get('confirmed')) is not bool:
            errors.append(f'{rid}: invalid resource type or confirmed flag')
        if resource.get('confirmed') is True:
            vram = resource.get('vram_gb')
            if resource.get('owner') not in MEMBERS or not resource.get('gpu_model') or type(vram) not in (int, float) or vram <= 0:
                errors.append(f'{rid}: confirm owner, GPU model and positive VRAM before approving slots')
    seen = set(); active = []
    for booking in schedule['reservations']:
        if not isinstance(booking, dict):
            errors.append('Booking must be an object'); continue
        bid = booking.get('booking_id')
        if not isinstance(bid, str) or not bid or bid in seen:
            errors.append('Booking IDs must be nonempty and unique'); continue
        seen.add(bid)
        resource = resources.get(booking.get('resource_id'))
        if resource is None:
            errors.append(f'{bid}: unknown resource'); continue
        if booking.get('member') not in MEMBERS or booking.get('status') not in STATUSES or not booking.get('purpose'):
            errors.append(f'{bid}: invalid member, status or missing purpose'); continue
        if resource.get('type') == 'colab' and booking['member'] != resource.get('owner'):
            errors.append(f'{bid}: Colab belongs to another member')
        try:
            start = datetime.fromisoformat(booking['start'])
            end = datetime.fromisoformat(booking['end'])
            if start.utcoffset() != timedelta(hours=7) or end.utcoffset() != timedelta(hours=7) or start >= end:
                raise ValueError('Expected positive interval with explicit +07:00 offset')
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f'{bid}: invalid start/end ({exc})'); continue
        if booking['status'] in ACTIVE:
            if resource.get('confirmed') is not True:
                errors.append(f'{bid}: resource is not confirmed')
            for other in active:
                if booking['resource_id'] == other[0] and start < other[2] and other[1] < end:
                    errors.append(f'{bid}: overlaps active booking {other[3]}')
            active.append((booking['resource_id'], start, end, bid))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default=str(ROOT / 'coordination/gpu_bookings.json'))
    args = parser.parse_args()
    try:
        schedule = load_json(Path(args.path))
        errors = validate_schedule(schedule)
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    for error in errors:
        print('FAIL:', error)
    if not errors:
        print(f'OK: {len(schedule["reservations"])} bookings; this does not reserve hardware or verify availability.')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
