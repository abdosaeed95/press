// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { afterEach, describe, expect, it, vi } from 'vitest';
import { dayjsCairo } from '../../utils/dayjs';
import SiteUpdateDistribution from './SiteUpdateDistribution.vue';

const { computed, methods } = SiteUpdateDistribution;

function context(values = {}) {
	const state = {
		distributionDays: 2,
		sites: [
			{ name: 'one.example.com' },
			{ name: 'two.example.com' },
			{ name: 'three.example.com' },
			{ name: 'four.example.com' },
		],
		siteSchedules: {},
		minimumTime: null,
		...values,
	};
	Object.defineProperty(state, 'canDistributeUpdateTimes', {
		get: () => computed.canDistributeUpdateTimes.call(state),
	});
	return state;
}

describe('Site update distribution', () => {
	afterEach(() => {
		vi.useRealTimers();
	});

	it('distributes site updates between 3 AM and 6 AM across entered days', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-07-27T12:00:00+03:00'));
		const state = context();

		methods.distributeSiteUpdateTimes.call(state);

		const times = Object.values(state.siteSchedules).map((schedule) =>
			dayjsCairo(schedule.scheduledTime)
		);
		expect(times.every((time) => time.hour() >= 3 && time.hour() < 6)).toBe(
			true
		);
		expect(times.every((time) => [0, 15, 30, 45].includes(time.minute()))).toBe(
			true
		);
		expect(new Set(times.map((time) => time.format('YYYY-MM-DD'))).size).toBe(
			2
		);
	});

	it('skips Friday and Saturday when distributing updates', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-08-06T12:00:00+03:00'));
		const state = context({
			distributionDays: 7,
			sites: Array.from({ length: 14 }, (_, index) => ({
				name: `${index}.example.com`,
			})),
		});

		methods.distributeSiteUpdateTimes.call(state);

		const times = Object.values(state.siteSchedules).map((schedule) =>
			dayjsCairo(schedule.scheduledTime)
		);
		expect(times[0].format('YYYY-MM-DD')).toBe('2026-08-09');
		expect(times.every((time) => ![5, 6].includes(time.day()))).toBe(true);
	});

	it('skips the final day through the 3rd across month boundaries', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-01-27T12:00:00+02:00'));
		const state = context({
			distributionDays: 10,
			sites: Array.from({ length: 16 }, (_, index) => ({
				name: `${index}.example.com`,
			})),
		});

		methods.distributeSiteUpdateTimes.call(state);

		const times = Object.values(state.siteSchedules).map((schedule) =>
			dayjsCairo(schedule.scheduledTime)
		);
		expect(
			times.some((time) => time.format('YYYY-MM-DD') === '2026-02-04')
		).toBe(true);
		expect(
			times.every(
				(time) => time.date() > 3 && time.date() !== time.daysInMonth()
			)
		).toBe(true);
	});

	it('starts after the blackout when tomorrow is the final day of a month', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-08-30T12:00:00+03:00'));
		const state = context({ distributionDays: 1 });

		methods.distributeSiteUpdateTimes.call(state);

		expect(
			Object.values(state.siteSchedules)[0].scheduledTime.startsWith(
				'2026-09-06'
			)
		).toBe(true);
	});

	it('moves distributed times after a late minimum time', () => {
		const minimumTime = dayjsCairo()
			.add(2, 'days')
			.startOf('day')
			.hour(5)
			.minute(30)
			.format('YYYY-MM-DDTHH:mm');
		const state = context({
			distributionDays: 1,
			minimumTime,
		});

		methods.distributeSiteUpdateTimes.call(state);

		expect(
			Object.values(state.siteSchedules).every((schedule) =>
				dayjsCairo(schedule.scheduledTime).isAfter(dayjsCairo(minimumTime))
			)
		).toBe(true);
	});

	it('shows the exact Cairo date and time after applying distribution', () => {
		expect(methods.formatSiteUpdateTime('2026-08-05T19:00')).toBe(
			'Wed, Aug 5, 2026 at 7:00 PM'
		);
	});
});
