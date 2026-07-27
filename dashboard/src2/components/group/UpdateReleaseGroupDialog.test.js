// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
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
});
