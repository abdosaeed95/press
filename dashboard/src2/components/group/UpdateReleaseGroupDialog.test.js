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

	it('marks and immediately selects sites without slaves', () => {
		const sites = [
			{ name: 'no-slave.example.com' },
			{ name: 'with-slave.example.com' },
		];
		const state = {
			benchDocResource: { doc: { deploy_information: { sites } } },
			deployInformation: { sites },
			selectedSites: [],
			siteSchedules: {},
			siteScheduledTime: '2026-07-28T03:00',
			slaveLookupComplete: false,
		};
		state.handleSiteSelection = methods.handleSiteSelection.bind(state);

		methods.handleSlaveLookupSuccess.call(state, ['no-slave.example.com']);

		expect(sites).toEqual([
			{ name: 'no-slave.example.com', no_slave: true },
			{ name: 'with-slave.example.com', no_slave: false },
		]);
		expect(state.selectedSites).toEqual([sites[0]]);
		expect(state.siteSchedules['no-slave.example.com'].updateTime).toBe(
			'after-deployment'
		);
		expect(state.slaveLookupComplete).toBe(true);
	});

	it('shows green No Slave and red Has a Slave badges', () => {
		const consoleColumn = computed.siteOptions
			.call({
				benchDocResource: {
					doc: { deploy_information: { sites: [] } },
				},
				useInPlaceUpdate: false,
			})
			.columns.find((column) => column.fieldname === 'no_slave');

		expect(consoleColumn.format(true)).toBe('No Slave');
		expect(consoleColumn.theme(true)).toBe('green');
		expect(consoleColumn.format(false)).toBe('Has a Slave');
		expect(consoleColumn.theme(false)).toBe('red');
	});

	it('shows team testing for the selected app release', () => {
		const release = {
			name: 'release-2',
			hash: '2222222',
			message: 'Second release',
			usage: { tested_days: 4, site_count: 2 },
		};
		const state = {
			benchDocResource: {
				doc: {
					deploy_information: {
						update_available: true,
						removed_apps: [],
						apps: [
							{
								name: 'frappe',
								title: 'Frappe',
								update_available: true,
								next_release: release.name,
								releases: [release],
								repository_url: 'https://github.com/frappe/frappe',
								current_hash: '1111111',
								will_branch_change: false,
							},
						],
					},
				},
			},
		};
		const options = computed.updatableAppOptions.call(state);
		const testingColumn = options.columns.find(
			(column) => column.label === 'Team testing'
		);
		const component = testingColumn.component({ row: options.data[0] });

		expect(component.props.release).toBe(release.name);
		expect(component.props.usage).toEqual(release.usage);
	});
});
