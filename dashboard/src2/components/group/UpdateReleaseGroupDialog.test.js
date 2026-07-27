// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
import DateTimeControl from '../DateTimeControl.vue';
import { dayjsCairo } from '../../utils/dayjs';
import UpdateReleaseGroupDialog from './UpdateReleaseGroupDialog.vue';

const { computed, methods } = UpdateReleaseGroupDialog;

function context(values = {}) {
	const deploymentScheduledTime = dayjsCairo()
		.add(1, 'day')
		.format('YYYY-MM-DDTHH:mm');
	const state = {
		deploymentTime: 'now',
		deploymentScheduledTime,
		siteScheduleMode: 'all',
		siteUpdateTime: 'after-deployment',
		siteScheduledTime: dayjsCairo(deploymentScheduledTime)
			.add(15, 'minute')
			.format('YYYY-MM-DDTHH:mm'),
		selectedSites: [{ name: 'one.example.com' }, { name: 'two.example.com' }],
		siteSchedules: {},
		...values,
	};

	state.isFutureUpdateTime = methods.isFutureUpdateTime.bind(state);
	state.isValidSiteUpdateTime = methods.isValidSiteUpdateTime.bind(state);
	Object.defineProperty(state, 'deployScheduledTime', {
		get: () => computed.deployScheduledTime.call(state),
	});
	return state;
}

describe('Update Bench Group scheduling', () => {
	it('defaults to per-site scheduling', () => {
		const state = UpdateReleaseGroupDialog.data();

		expect(state.siteScheduleMode).toBe('per-site');
		expect(state.distributionDays).toBeNull();
	});

	it('makes every distributed day selectable', () => {
		const options = DateTimeControl.computed.dayOptions.call({
			days: 11,
			minimumTime: null,
		});

		expect(options).toHaveLength(11);
	});

	it('deploys now and updates all sites after deployment', () => {
		const state = context();

		expect(computed.updateTimesAreValid.call(state)).toBe(true);
		expect(computed.deployScheduledTime.call(state)).toBeNull();
		expect(computed.sitesForUpdate.call(state)).toEqual([
			{ name: 'one.example.com', scheduled_time: null },
			{ name: 'two.example.com', scheduled_time: null },
		]);
	});

	it('keeps a shared site update later than a scheduled deployment', () => {
		const state = context({
			deploymentTime: 'scheduled',
			siteUpdateTime: 'scheduled',
		});

		expect(computed.updateTimesAreValid.call(state)).toBe(true);
		expect(computed.sitesForUpdate.call(state)[0].scheduled_time).toBe(
			state.siteScheduledTime
		);
	});

	it('supports mixed per-site update times', () => {
		const scheduledTime = dayjsCairo()
			.add(2, 'days')
			.format('YYYY-MM-DDTHH:mm');
		const state = context({
			siteScheduleMode: 'per-site',
			siteSchedules: {
				'one.example.com': {
					updateTime: 'after-deployment',
					scheduledTime: '',
				},
				'two.example.com': {
					updateTime: 'scheduled',
					scheduledTime,
				},
			},
		});

		expect(computed.updateTimesAreValid.call(state)).toBe(true);
		expect(computed.sitesForUpdate.call(state)).toEqual([
			{ name: 'one.example.com', scheduled_time: null },
			{ name: 'two.example.com', scheduled_time: scheduledTime },
		]);
	});

	it('rejects a site update before the scheduled deployment', () => {
		const state = context({
			deploymentTime: 'scheduled',
			siteUpdateTime: 'scheduled',
		});
		state.siteScheduledTime = dayjsCairo(state.deploymentScheduledTime)
			.subtract(15, 'minute')
			.format('YYYY-MM-DDTHH:mm');

		expect(computed.updateTimesAreValid.call(state)).toBe(false);
	});

	it('distributes site updates between 3 AM and 6 AM across entered days', () => {
		const state = context({
			distributionDays: 2,
			selectedSites: [
				{ name: 'one.example.com' },
				{ name: 'two.example.com' },
				{ name: 'three.example.com' },
				{ name: 'four.example.com' },
			],
			siteSchedules: {},
		});
		Object.defineProperty(state, 'canDistributeUpdateTimes', {
			get: () => computed.canDistributeUpdateTimes.call(state),
		});

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
		expect(
			Object.values(state.siteSchedules).every(
				(schedule) => schedule.updateTime === 'scheduled'
			)
		).toBe(true);
	});

	it('moves distributed times after a late scheduled deployment', () => {
		const deploymentScheduledTime = dayjsCairo()
			.add(2, 'days')
			.startOf('day')
			.hour(5)
			.minute(30)
			.format('YYYY-MM-DDTHH:mm');
		const state = context({
			deploymentTime: 'scheduled',
			deploymentScheduledTime,
			distributionDays: 1,
			siteSchedules: {},
		});
		Object.defineProperty(state, 'canDistributeUpdateTimes', {
			get: () => computed.canDistributeUpdateTimes.call(state),
		});

		methods.distributeSiteUpdateTimes.call(state);

		expect(
			Object.values(state.siteSchedules).every((schedule) =>
				dayjsCairo(schedule.scheduledTime).isAfter(
					dayjsCairo(deploymentScheduledTime)
				)
			)
		).toBe(true);
	});

	it('shows the exact Cairo date and time after applying distribution', () => {
		expect(methods.formatSiteUpdateTime('2026-08-05T19:00')).toBe(
			'Wed, Aug 5, 2026 at 7:00 PM'
		);
	});
});
