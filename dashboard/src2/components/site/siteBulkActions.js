// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { defineAsyncComponent, h } from 'vue';
import { toast } from 'vue-sonner';
import { confirmDialog, renderDialog } from '../../utils/components';
import { cairoTimeToServer } from '../../utils/dayjs';
import { getToastErrorMessage } from '../../utils/toast';

export async function scheduleSelectedSites(listResource, sites) {
	await Promise.all(
		sites.map((site) =>
			listResource.runDocMethod.submit({
				name: site.name,
				method: 'schedule_update',
				scheduled_time: cairoTimeToServer(site.scheduled_time).format(
					'YYYY-MM-DDTHH:mm'
				),
			})
		)
	);
	await listResource.reload();
}

export async function cancelSelectedSiteUpdates(listResource, sites) {
	await Promise.all(
		sites.map((site) =>
			listResource.runDocMethod.submit({
				name: site.name,
				method: 'cancel_scheduled_update',
				site_update: site.scheduled_update,
			})
		)
	);
	await listResource.reload();
}

export function getSiteBulkActions(listResource, selectedRows) {
	const updatableSites = selectedRows.filter(
		(site) =>
			site.status === 'Update Available' &&
			['Active', 'Inactive', 'Suspended'].includes(site.site_status)
	);
	const scheduledSites = selectedRows.filter(
		(site) => site.status === 'Scheduled'
	);
	const options = [];

	if (updatableSites.length) {
		options.push({
			label: `Schedule Updates (${updatableSites.length})`,
			icon: 'calendar',
			onClick() {
				const BulkSiteUpdateDialog = defineAsyncComponent(() =>
					import('./BulkSiteUpdateDialog.vue')
				);
				renderDialog(
					h(BulkSiteUpdateDialog, {
						sites: updatableSites,
						submitUpdates(updates) {
							const promise = scheduleSelectedSites(listResource, updates);
							toast.promise(promise, {
								loading: 'Scheduling site updates...',
								success: `${updates.length} site update${
									updates.length === 1 ? '' : 's'
								} scheduled`,
								error: (error) => getToastErrorMessage(error),
							});
							return promise;
						},
					})
				);
			},
		});
	}

	if (scheduledSites.length) {
		options.push({
			label: `Cancel Scheduled Updates (${scheduledSites.length})`,
			icon: 'x',
			onClick() {
				confirmDialog({
					title: 'Cancel Scheduled Updates',
					message: `Cancel the scheduled update for ${
						scheduledSites.length
					} site${scheduledSites.length === 1 ? '' : 's'}?`,
					onSuccess({ hide }) {
						const promise = cancelSelectedSiteUpdates(
							listResource,
							scheduledSites
						);
						toast.promise(promise, {
							loading: 'Cancelling scheduled updates...',
							success: () => {
								hide();
								return `${scheduledSites.length} scheduled update${
									scheduledSites.length === 1 ? '' : 's'
								} cancelled`;
							},
							error: (error) => getToastErrorMessage(error),
						});
						return promise;
					},
				});
			},
		});
	}

	return options.length
		? [
				{
					label: 'Bulk Actions',
					showLabel: true,
					options,
				},
		  ]
		: [];
}
