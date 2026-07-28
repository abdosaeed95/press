<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<Button
		v-if="usage?.site_count"
		variant="ghost"
		:label="testedLabel"
		@click="openDetails"
	/>
	<Badge v-else label="Not tested by your team" theme="gray" />
	<Dialog
		v-if="usage?.site_count"
		v-model="showDetails"
		:options="{ title: 'Sites using this version', size: '2xl' }"
	>
		<template #body-content>
			<div class="space-y-4">
				<div class="grid grid-cols-2 gap-3">
					<div class="rounded border p-3">
						<p class="text-sm text-gray-600">Tested since</p>
						<p class="mt-1 font-medium">
							{{ formatDate(usage.testing_since) }}
						</p>
					</div>
					<div class="rounded border p-3">
						<p class="text-sm text-gray-600">Oldest site created</p>
						<p class="mt-1 font-medium">
							{{ formatDate(usage.oldest_site_date) }}
						</p>
					</div>
				</div>
				<LoadingText
					v-if="$resources.details.loading"
					text="Loading team sites"
				/>
				<div
					v-else-if="sites.length"
					class="max-h-80 overflow-y-auto rounded border"
				>
					<div
						class="sticky top-0 grid grid-cols-3 gap-3 border-b bg-gray-50 px-3 py-2 text-xs font-medium text-gray-600"
					>
						<span>Site</span>
						<span>Using since</span>
						<span>Created</span>
					</div>
					<div
						v-for="site in sites"
						:key="site.name"
						class="grid grid-cols-3 gap-3 border-b px-3 py-2 text-sm last:border-b-0"
					>
						<router-link
							class="font-medium text-gray-900 hover:underline"
							:to="{ name: 'Site Detail', params: { name: site.name } }"
						>
							{{ site.name }}
						</router-link>
						<span>{{ formatDate(site.using_since) }}</span>
						<span>{{ formatDate(site.creation) }}</span>
					</div>
				</div>
				<p v-else class="py-6 text-center text-sm text-gray-600">
					No sites in your team currently use this version.
				</p>
			</div>
		</template>
	</Dialog>
</template>

<script>
import { date } from '../../utils/format';

export default {
	name: 'ReleaseUsage',
	props: {
		release: String,
		usage: Object,
	},
	data() {
		return {
			showDetails: false,
		};
	},
	resources: {
		details() {
			return {
				url: 'press.api.bench.release_usage',
				initialData: { sites: [] },
			};
		},
	},
	computed: {
		testedLabel() {
			const days = this.usage.tested_days;
			return `Tested for ${days} ${days === 1 ? 'day' : 'days'}`;
		},
		sites() {
			return this.$resources.details.data?.sites || [];
		},
	},
	methods: {
		openDetails() {
			this.showDetails = true;
			this.$resources.details.submit({ release: this.release });
		},
		formatDate(value) {
			return date(value, 'lll');
		},
	},
};
</script>
