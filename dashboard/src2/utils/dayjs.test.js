// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { afterEach, describe, expect, it, vi } from 'vitest';
import { scheduledTimeLabel } from './dayjs';

describe('scheduledTimeLabel', () => {
	afterEach(() => {
		vi.useRealTimers();
	});

	it('shows the next weekday and Cairo time', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-07-27T12:00:00+03:00'));

		expect(scheduledTimeLabel('2026-08-05 21:30:00')).toBe(
			'Next Wed, Aug 5 at 7:00 PM'
		);
	});
});
