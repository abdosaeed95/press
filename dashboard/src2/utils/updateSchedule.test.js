// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, test } from 'vitest';
import { dayjsLocal } from './dayjs';
import {
	getCalendarDays,
	getCalendarRange,
	getRescheduledTime,
	groupUpdatesByDay,
} from './updateSchedule';

describe('update schedule calendar', () => {
	test('builds a six-week Sunday-first calendar', () => {
		const days = getCalendarDays('2026-07-01');
		const range = getCalendarRange('2026-07-01');

		expect(days).toHaveLength(42);
		expect(days[0].key).toBe('2026-06-28');
		expect(days[41].key).toBe('2026-08-08');
		expect(range.end.diff(range.start, 'day')).toBe(42);
	});

	test('groups stored update times by Cairo day', () => {
		const grouped = groupUpdatesByDay([
			{
				name: 'UPDATE-1',
				event_time: '2026-07-29 01:00:00',
			},
		]);

		expect(grouped['2026-07-28'][0].name).toBe('UPDATE-1');
	});

	test('preserves the Cairo time when an update changes day', () => {
		const scheduled_time = getRescheduledTime(
			{ scheduled_time: '2026-07-29 06:30:00' },
			'2026-08-02'
		);

		expect(scheduled_time.format('YYYY-MM-DD')).toBe('2026-08-02');
		expect(scheduled_time.format('HH:mm')).toBe(
			dayjsLocal('2026-07-29 06:30:00').format('HH:mm')
		);
	});
});
