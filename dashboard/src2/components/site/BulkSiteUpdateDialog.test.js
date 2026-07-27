// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { afterEach, describe, expect, it, vi } from 'vitest';
import BulkSiteUpdateDialog from './BulkSiteUpdateDialog.vue';

describe('Bulk site update dialog', () => {
	afterEach(() => {
		vi.useRealTimers();
	});

	it('requires a future time for every selected site', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-07-27T12:00:00+03:00'));
		const state = {
			sites: [{ name: 'one.example.com' }, { name: 'two.example.com' }],
			siteSchedules: {
				'one.example.com': {
					updateTime: 'scheduled',
					scheduledTime: '2026-07-28T03:00',
				},
				'two.example.com': {
					updateTime: 'scheduled',
					scheduledTime: '',
				},
			},
		};

		expect(BulkSiteUpdateDialog.computed.canSchedule.call(state)).toBeFalsy();
		state.siteSchedules['two.example.com'].scheduledTime = '2026-07-28T03:15';
		expect(BulkSiteUpdateDialog.computed.canSchedule.call(state)).toBe(true);
	});

	it('submits the exact selected site times', async () => {
		const submitUpdates = vi.fn().mockResolvedValue();
		const state = {
			sites: [{ name: 'one.example.com' }, { name: 'two.example.com' }],
			siteSchedules: {
				'one.example.com': {
					updateTime: 'scheduled',
					scheduledTime: '2026-07-28T03:00',
				},
				'two.example.com': {
					updateTime: 'scheduled',
					scheduledTime: '2026-07-28T03:15',
				},
			},
			canSchedule: true,
			submitUpdates,
			loading: false,
			errorMessage: '',
			show: true,
		};

		await BulkSiteUpdateDialog.methods.scheduleUpdates.call(state);

		expect(submitUpdates).toHaveBeenCalledWith([
			{ name: 'one.example.com', scheduled_time: '2026-07-28T03:00' },
			{ name: 'two.example.com', scheduled_time: '2026-07-28T03:15' },
		]);
		expect(state.show).toBe(false);
	});
});
