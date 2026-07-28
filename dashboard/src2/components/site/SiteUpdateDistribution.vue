<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<div class="space-y-3">
		<div class="rounded-lg border bg-gray-50 p-3">
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
				<FormControl
					label="Number of days"
					type="number"
					:min="1"
					placeholder="Enter days"
					v-model.number="distributionDays"
				/>
				<Button
					label="Apply"
					:disabled="!canDistributeUpdateTimes"
					@click="distributeSiteUpdateTimes"
				/>
			</div>
			<p class="mt-2 text-sm text-gray-600">
				Distribute selected sites between 3 AM and 6 AM Cairo time. Friday and
				Saturday are skipped.
			</p>
		</div>
		<div class="max-h-72 space-y-3 overflow-y-auto">
			<div
				v-for="site in sites"
				:key="site.name"
				class="space-y-3 rounded-lg border p-3"
			>
				<p class="font-medium text-gray-900">{{ site.name }}</p>
				<p
					v-if="
						siteSchedules[site.name].updateTime === 'scheduled' &&
						siteSchedules[site.name].scheduledTime
					"
					class="text-sm font-medium text-gray-700"
				>
					Expected update:
					{{ formatSiteUpdateTime(siteSchedules[site.name].scheduledTime) }}
					(Cairo)
				</p>
				<FormControl
					v-if="!scheduleOnly"
					label="Site update time"
					type="select"
					:options="siteUpdateTimeOptions"
					v-model="siteSchedules[site.name].updateTime"
				/>
				<DateTimeControl
					v-if="siteSchedules[site.name].updateTime === 'scheduled'"
					v-model="siteSchedules[site.name].scheduledTime"
					label="Site update time (Cairo)"
					:minimum-time="minimumTime"
					:days="distributionDays ? distributionDays + 1 : 7"
				/>
			</div>
		</div>
	</div>
</template>

<script>
import { dayjsCairo, distributeSiteUpdateTimes } from '../../utils/dayjs';
import DateTimeControl from '../DateTimeControl.vue';

export default {
	name: 'SiteUpdateDistribution',
	components: {
		DateTimeControl,
	},
	props: {
		sites: {
			type: Array,
			required: true,
		},
		siteSchedules: {
			type: Object,
			required: true,
		},
		minimumTime: String,
		scheduleOnly: Boolean,
	},
	data() {
		return {
			distributionDays: null,
		};
	},
	computed: {
		siteUpdateTimeOptions() {
			return [
				{ label: 'Update after deployment', value: 'after-deployment' },
				{ label: 'Schedule', value: 'scheduled' },
			];
		},
		canDistributeUpdateTimes() {
			return (
				Number.isInteger(this.distributionDays) &&
				this.distributionDays > 0 &&
				this.sites.length > 0
			);
		},
	},
	methods: {
		distributeSiteUpdateTimes() {
			if (!this.canDistributeUpdateTimes) {
				return;
			}

			Object.assign(
				this.siteSchedules,
				distributeSiteUpdateTimes(
					this.sites,
					this.distributionDays,
					this.minimumTime
				)
			);
		},
		formatSiteUpdateTime(time) {
			return dayjsCairo(time).format('ddd, MMM D, YYYY [at] h:mm A');
		},
	},
};
</script>
