// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
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
	it('distributes site updates between 3 AM and 6 AM across entered days', () => {
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
