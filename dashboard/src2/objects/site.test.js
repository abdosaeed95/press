// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it, vi } from 'vitest';
import {
	cancelSelectedSiteUpdates,
	getSiteBulkActions,
	scheduleSelectedSites,
} from '../components/site/siteBulkActions';

describe('Site list bulk updates', () => {
	it('shows actions for eligible selected rows', () => {
		const actions = getSiteBulkActions({}, [
			{
				name: 'available.example.com',
				status: 'Update Available',
				site_status: 'Active',
			},
			{
				name: 'scheduled.example.com',
				status: 'Scheduled',
				scheduled_update: 'scheduled-update',
			},
		]);

		expect(actions).toHaveLength(1);
		expect(actions[0].label).toBe('Bulk Actions');
		expect(actions[0].showLabel).toBe(true);
		expect(actions[0].options.map((action) => action.label)).toEqual([
			'Schedule Updates (1)',
			'Cancel Scheduled Updates (1)',
		]);
	});

	it('schedules selected sites with server-timezone values', async () => {
		const listResource = {
			runDocMethod: { submit: vi.fn().mockResolvedValue() },
			reload: vi.fn().mockResolvedValue(),
		};

		await scheduleSelectedSites(listResource, [
			{
				name: 'available.example.com',
				scheduled_time: '2026-07-28T03:00',
			},
		]);

		expect(listResource.runDocMethod.submit).toHaveBeenCalledWith({
			name: 'available.example.com',
			method: 'schedule_update',
			scheduled_time: '2026-07-28T05:30',
		});
		expect(listResource.reload).toHaveBeenCalledOnce();
	});

	it('cancels each selected scheduled update', async () => {
		const listResource = {
			runDocMethod: { submit: vi.fn().mockResolvedValue() },
			reload: vi.fn().mockResolvedValue(),
		};

		await cancelSelectedSiteUpdates(listResource, [
			{
				name: 'scheduled.example.com',
				scheduled_update: 'scheduled-update',
			},
		]);

		expect(listResource.runDocMethod.submit).toHaveBeenCalledWith({
			name: 'scheduled.example.com',
			method: 'cancel_scheduled_update',
			site_update: 'scheduled-update',
		});
		expect(listResource.reload).toHaveBeenCalledOnce();
	});
});
