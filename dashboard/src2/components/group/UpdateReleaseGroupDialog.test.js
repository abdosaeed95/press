// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { afterEach, describe, expect, it, vi } from 'vitest';
import DateTimeControl from '../DateTimeControl.vue';
import { cairoTimeToServer, dayjsCairo } from '../../utils/dayjs';
import UpdateReleaseGroupDialog from './UpdateReleaseGroupDialog.vue';

const { computed, methods, watch } = UpdateReleaseGroupDialog;

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
	state.isValidPreservedSiteUpdateTime =
		methods.isValidPreservedSiteUpdateTime.bind(state);
	Object.defineProperty(state, 'deployScheduledTime', {
		get: () => computed.deployScheduledTime.call(state),
	});
	Object.defineProperty(state, 'preservedScheduledSites', {
		get: () => computed.preservedScheduledSites.call(state),
	});
	Object.defineProperty(state, 'sitesForScheduling', {
		get: () => computed.sitesForScheduling.call(state),
	});
	return state;
}

describe('Update Bench Group scheduling', () => {
	afterEach(() => {
		vi.useRealTimers();
	});

	it('defaults to per-site scheduling', () => {
		const state = UpdateReleaseGroupDialog.data();

		expect(state.siteScheduleMode).toBe('per-site');
		expect(state.includeScheduledSites).toBe(false);
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

	it('selects sites without slaves and schedules the next Cairo window', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-07-29T16:00:00+03:00'));
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
			includeScheduledSites: false,
			deployScheduledTime: null,
			slaveLookupComplete: false,
		};
		Object.defineProperty(state, 'sitesForScheduling', {
			get: () => computed.sitesForScheduling.call(state),
		});
		state.handleSiteSelection = methods.handleSiteSelection.bind(state);
		state.scheduleNoSlaveSites = methods.scheduleNoSlaveSites.bind(state);

		methods.handleSlaveLookupSuccess.call(state, ['no-slave.example.com']);

		expect(sites).toEqual([
			{ name: 'no-slave.example.com', no_slave: true },
			{ name: 'with-slave.example.com', no_slave: false },
		]);
		expect(state.selectedSites).toEqual([sites[0]]);
		expect(state.siteSchedules['no-slave.example.com']).toEqual({
			updateTime: 'scheduled',
			scheduledTime: '2026-07-30T04:30',
		});
		expect(state.slaveLookupComplete).toBe(true);
	});

	it('moves a no-slave site to the next working window after deployment', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-07-29T16:00:00+03:00'));
		const site = { name: 'no-slave.example.com', no_slave: true };
		const state = context({
			selectedSites: [site],
			siteSchedules: {},
			deploymentTime: 'scheduled',
			deploymentScheduledTime: '2026-07-30T16:00',
		});

		methods.scheduleNoSlaveSites.call(state);

		expect(state.siteSchedules[site.name]).toEqual({
			updateTime: 'scheduled',
			scheduledTime: '2026-08-02T04:30',
		});
	});

	it('keeps scheduled sites excluded until the option is enabled', () => {
		const sites = [
			{ name: 'regular.example.com' },
			{
				name: 'scheduled.example.com',
				scheduled_update: 'site-update-1',
			},
		];
		const base = {
			benchDocResource: { doc: { deploy_information: { sites } } },
			useInPlaceUpdate: false,
		};

		expect(
			computed.siteOptions.call({
				...base,
				includeScheduledSites: false,
			}).data
		).toEqual([sites[0]]);
		expect(
			computed.siteOptions.call({
				...base,
				includeScheduledSites: true,
			}).data
		).toEqual(sites);
	});

	it('selects scheduled sites without changing their existing time', () => {
		const scheduledTime = cairoTimeToServer(
			dayjsCairo().add(2, 'days').format('YYYY-MM-DDTHH:mm')
		).format('YYYY-MM-DD HH:mm:ss');
		const sites = [
			{ name: 'regular.example.com' },
			{
				name: 'scheduled.example.com',
				scheduled_update: 'site-update-1',
				scheduled_time: scheduledTime,
			},
		];
		const state = {
			benchDocResource: { doc: { deploy_information: { sites } } },
			selectedSites: [sites[0]],
			scheduledSites: [sites[1]],
			siteSchedules: {},
			siteScheduledTime: '2026-07-28T03:00',
			includeScheduledSites: true,
		};
		Object.defineProperty(state, 'sitesForScheduling', {
			get: () => computed.sitesForScheduling.call(state),
		});
		state.handleSiteSelection = methods.handleSiteSelection.bind(state);

		watch.includeScheduledSites.call(state, true);

		expect(state.selectedSites).toEqual(sites);
		expect(state.selectedSites[1].scheduled_time).toBe(scheduledTime);
		expect(state.siteSchedules['scheduled.example.com']).toBeUndefined();
	});

	it('preserves the existing schedule and marks it for retargeting', () => {
		const scheduledTime = cairoTimeToServer(
			dayjsCairo().add(2, 'days').format('YYYY-MM-DDTHH:mm')
		).format('YYYY-MM-DD HH:mm:ss');
		const scheduledSite = {
			name: 'scheduled.example.com',
			scheduled_update: 'site-update-1',
			scheduled_time: scheduledTime,
		};
		const state = context({ selectedSites: [scheduledSite] });

		expect(computed.updateTimesAreValid.call(state)).toBe(true);
		expect(computed.sitesForUpdate.call(state)).toEqual([
			{
				...scheduledSite,
				preserve_scheduled_update: true,
			},
		]);
	});

	it('rejects a preserved site time before the bench deployment', () => {
		const siteTime = dayjsCairo().add(2, 'days');
		const state = context({
			deploymentTime: 'scheduled',
			deploymentScheduledTime: siteTime
				.add(1, 'hour')
				.format('YYYY-MM-DDTHH:mm'),
			selectedSites: [
				{
					name: 'scheduled.example.com',
					scheduled_update: 'site-update-1',
					scheduled_time: cairoTimeToServer(
						siteTime.format('YYYY-MM-DDTHH:mm')
					).format('YYYY-MM-DD HH:mm:ss'),
				},
			],
		});

		expect(computed.updateTimesAreValid.call(state)).toBe(false);
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
