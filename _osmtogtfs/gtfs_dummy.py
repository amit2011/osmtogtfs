"""Tools to generate dummy GTFS feeds."""
import datetime
import logging


def create_dummy_calendar():
    return [{'service_id': 'WE', 'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0,
             'friday': 0, 'saturday': 1, 'sunday': 1, 'start_date': 20170101, 'end_date': 20190101},
            {'service_id': 'WD', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 0, 'sunday': 0, 'start_date': 20170101, 'end_date': 20190101}]


def create_dummy_trips_and_stoptimes(routes, route_stops, calendar):
    trips = []
    stoptimes = []
    for route_id, route in routes.items():
        if len(route_stops.get(route_id, [])) < 2:
            continue
        for cal in calendar:
        # For the sake of simplicity, we assume a fixed number of trips per service day.
        # Even though in reality there are less number of trips on weekends and holidays.
        # We assume trips begin from 5:00 AM and run untill 11:00 PM and there is one trip
        # every 20 minutes. Therefore in total we add 54 trips per route per service day.
        # 18 service hours per day * 3 trips per hour = 54
            for idx in range(54):

                trip_id = \
                    '{route_id}{service_id}{sequence}'.format(route_id=route_id,
                        service_id=cal['service_id'],
                        sequence=idx+1)

                trip = {'route_id': route_id,
                        'service_id': cal['service_id'],
                        'trip_id': trip_id,
                        'trip_headsign': '[Dummy]{}'.format(route['route_long_name']),
                        'shape_id': route_id}
                trips.append(trip)

                stoptimes.extend(
                    _create_dummy_trip_stoptimes(trip_id,
                        route_stops.get(route_id, []),
                        idx))

    return trips, stoptimes


def _create_dummy_trip_stoptimes(trip_id, stop_ids, sequence):
    """Create station stop times for each trip."""
    delta = datetime.timedelta(minutes=20)
    offset = sequence*delta
    waiting = datetime.timedelta(seconds=30)

    first_service_time = datetime.datetime(2017, 1, 1, 5, 0, 0) + offset

    stop_sequence = 0
    arrival = first_service_time
    last_departure_hour = (arrival + waiting).hour

    for stop_id in stop_ids:

        departure = arrival + waiting

        if arrival.hour < last_departure_hour:
            arrival_hour = arrival.hour + 24
            departure_hour = departure.hour + 24
            last_departure_hour = departure.hour + 24
        else:
            arrival_hour = arrival.hour
            departure_hour = departure.hour
            last_departure_hour = departure.hour

        yield {'trip_id': trip_id,
               'arrival_time': '{:02}:{}'.format(arrival_hour, arrival.strftime('%M:%S')),
               'departure_time': '{:02}:{}'.format(departure_hour, departure.strftime('%M:%S')),
               'stop_id': stop_id,
               'stop_sequence': stop_sequence}

        stop_sequence += 1
        arrival += delta
