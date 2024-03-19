import unittest
from datetime import datetime

from base.bookings.sync import find_missing_bookings


class TestFindMissingBookings(unittest.TestCase):
    # %Y-%m-%d %H:%M:%S
    def test_missing_bookings(self):
        db_bookings = [
            {'passageTime': datetime(2024, 3, 18, 10, 30), 'id': 1},
            {'passageTime': datetime(2024, 3, 18, 12, 45), 'id': 2},
            {'passageTime': datetime(2024, 3, 19, 9, 0), 'id': 3}
        ]

        device_bookings = [
            {'passageTime': '2024-03-18 10:30:00', 'id': 4},
            {'passageTime': '2024-03-19 11:15:00', 'id': 5},
            {'passageTime': '2024-03-19 14:30:00', 'id': 6}
        ]

        expected_missing_bookings = [
            {'passageTime': '2024-03-19 11:15:00', 'id': 5},
            {'passageTime': '2024-03-19 14:30:00', 'id': 6}
        ]

        missing_bookings = find_missing_bookings(db_bookings, device_bookings)
        self.assertEqual(missing_bookings, expected_missing_bookings)


if __name__ == '__main__':
    unittest.main()
