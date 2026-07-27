<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<Dialog
		v-model="show"
		:options="{
			title: `Schedule ${sites.length} site${sites.length === 1 ? '' : 's'}`,
			size: '2xl',
		}"
	>
		<template #body-content>
			<SiteUpdateDistribution
				:sites="sites"
				:site-schedules="siteSchedules"
				schedule-only
			/>
			<ErrorMessage class="mt-4" :message="errorMessage" />
		</template>
		<template #actions>
			<Button
				class="w-full"
				variant="solid"
				:label="`Schedule ${sites.length} site${sites.length === 1 ? '' : 's'}`"
				:disabled="!canSchedule"
				:loading="loading"
				@click="scheduleUpdates"
			/>
		</template>
	</Dialog>
</template>

<script>
import { dayjsCairo } from '../../utils/dayjs';
import { getToastErrorMessage } from '../../utils/toast';
import SiteUpdateDistribution from './SiteUpdateDistribution.vue';

export default {
	name: 'BulkSiteUpdateDialog',
	components: {
		SiteUpdateDistribution,
	},
	props: {
		sites: {
			type: Array,
			required: true,
		},
		submitUpdates: {
			type: Function,
			required: true,
		},
	},
	data() {
		return {
			show: true,
			loading: false,
			errorMessage: '',
			siteSchedules: Object.fromEntries(
				this.sites.map((site) => [
					site.name,
					{ updateTime: 'scheduled', scheduledTime: '' },
				])
			),
		};
	},
	computed: {
		canSchedule() {
			return this.sites.every((site) => {
				const time = this.siteSchedules[site.name].scheduledTime;
				return time && dayjsCairo(time).isAfter(dayjsCairo());
			});
		},
	},
	methods: {
		async scheduleUpdates() {
			if (!this.canSchedule) {
				return;
			}

			this.loading = true;
			this.errorMessage = '';
			try {
				await this.submitUpdates(
					this.sites.map((site) => ({
						name: site.name,
						scheduled_time: this.siteSchedules[site.name].scheduledTime,
					}))
				);
				this.show = false;
			} catch (error) {
				this.errorMessage = getToastErrorMessage(error);
			} finally {
				this.loading = false;
			}
		},
	},
};
</script>
