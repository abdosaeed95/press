<template>
	<div v-if="availableApps.length" class="space-y-12">
		<div class="flex justify-end">
			<Button
				:label="isAllSelected ? 'Deselect All Apps' : 'Select All Apps'"
				variant="ghost"
				:disabled="showAppPlanSelectorDialog"
				@click="toggleAllApps"
			/>
		</div>
		<div v-if="publicApps">
			<h2 class="text-sm font-medium leading-6 text-gray-900">
				{{
					!siteOnPublicBench && privateApps
						? 'Select Marketplace Apps'
						: 'Select Apps'
				}}
			</h2>
			<div class="mt-2 w-full space-y-2">
				<ObjectList :options="publicApps" />
			</div>
			<SiteAppPlanSelectorDialog
				v-if="selectedApp"
				v-model="showAppPlanSelectorDialog"
				:app="selectedApp"
				@plan-select="selectAppPlan"
			/>
		</div>
		<div v-if="!siteOnPublicBench && privateApps">
			<h2 class="text-sm font-medium leading-6 text-gray-900">
				Select Private Apps
			</h2>
			<div class="mt-2 w-full space-y-2">
				<ObjectList :options="privateApps" />
			</div>
		</div>
	</div>
</template>

<script>
import { h } from 'vue';
import DownloadIcon from '~icons/lucide/download';
import SiteAppPlanSelectorDialog from './SiteAppPlanSelectorDialog.vue';
import { Badge, Button } from 'frappe-ui';
import { icon } from '../../utils/components';
import ObjectList from '../ObjectList.vue';
import { toast } from 'vue-sonner';

export default {
	props: ['availableApps', 'siteOnPublicBench', 'modelValue'],
	emits: ['update:modelValue'],
	components: {
		Button,
		ObjectList,
		SiteAppPlanSelectorDialog,
	},
	data() {
		return {
			selectedApp: null,
			showAppPlanSelectorDialog: false,
			pendingPlanApps: [],
			continuePlanSelection: false,
		};
	},
	watch: {
		availableApps: {
			immediate: true,
			handler(availableApps) {
				const selectedApps = new Set(this.apps.map(this.getAppName));
				const preinstalledApps = (availableApps || []).filter(
					(app) => app.preinstalled && !selectedApps.has(this.getAppName(app))
				);
				if (preinstalledApps.length)
					this.apps = [...this.apps, ...preinstalledApps];
			},
		},
		showAppPlanSelectorDialog(show) {
			if (show) return;
			if (this.continuePlanSelection) {
				this.continuePlanSelection = false;
				this.$nextTick(this.openNextPlanSelector);
				return;
			}
			this.pendingPlanApps = [];
			this.selectedApp = null;
		},
	},
	computed: {
		apps: {
			get() {
				return this.modelValue || [];
			},
			set(newApps) {
				this.$emit('update:modelValue', newApps);
			},
		},
		isAllSelected() {
			const selectedApps = new Set(this.apps.map(this.getAppName));
			return this.availableApps.every((app) =>
				selectedApps.has(this.getAppName(app))
			);
		},
		publicApps() {
			if (!this.availableApps) return;
			const publicApps = this.availableApps.filter(
				(app) => (app.public || app.plans?.length) && app.image
			);

			if (!publicApps.length) return;

			return {
				data: () => publicApps,
				columns: [
					{
						label: 'App',
						fieldname: 'app_title',
						type: 'Component',
						component: ({ row }) => {
							return h(
								'a',
								{
									class: 'flex items-center text-sm',
									href: `/${row.route}`,
									target: '_blank',
								},
								[
									h('img', {
										class: 'h-6 w-6 rounded-sm',
										src: row.image,
									}),
									h('span', { class: 'ml-2' }, row.title || row.app_title),
									row?.preinstalled
										? h(Badge, {
												class: 'ml-2',
												theme: 'green',
												label: 'Pre-Installed',
										  })
										: '',
									row.subscription_type !== 'Free'
										? h(Badge, {
												class: 'ml-2',
												theme: 'gray',
												label: 'Paid',
										  })
										: '',
								]
							);
						},
					},
					{
						label: 'Installs',
						width: 0.2,
						type: 'Component',
						component: ({ row }) => {
							return h(
								'div',
								{
									class: 'flex items-center text-sm text-gray-600',
								},
								[
									h(DownloadIcon, {
										class: 'h-3 w-3',
									}),
									h('span', { class: 'ml-0.5 leading-3' }, [
										this.$format.numberK(row.total_installs || '0'),
									]),
								]
							);
						},
					},
					{
						label: '',
						width: 0.2,
						align: 'right',
						type: 'Button',
						Button: ({ row: app }) => {
							const isAppAdded = this.apps.map((a) => a.app).includes(app.app);

							return {
								label: isAppAdded ? 'check' : 'plus',
								slots: {
									icon: isAppAdded ? icon('check') : icon('plus'),
								},
								variant: isAppAdded ? 'outline' : 'subtle',
								onClick: (event) => {
									this.toggleApp(app);
									event.stopPropagation();
								},
							};
						},
					},
				],
			};
		},
		privateApps() {
			if (!this.availableApps) return;

			let privateApps = this.availableApps.filter(
				(app) => !((app.public || app.plans?.length) && app.image)
			);

			if (privateApps.length === 0) return;

			return {
				data: () => privateApps,
				columns: [
					{
						label: 'App',
						fieldname: 'app_title',
					},
					{
						label: '',
						align: 'right',
						type: 'Button',
						Button: ({ row: app }) => {
							const isAppAdded = this.apps
								.map((a) => a.app)
								.includes(app.app || app.app_title);
							return {
								label: 'Add',
								slots: {
									icon: isAppAdded ? icon('check') : icon('plus'),
								},
								variant: isAppAdded ? 'outline' : 'subtle',
								onClick: (event) => {
									this.toggleApp(app);
									event.stopPropagation();
								},
							};
						},
					},
				],
			};
		},
	},
	methods: {
		getAppName(app) {
			return app.app || app.app_title;
		},
		requiresPlan(app) {
			return (
				app.subscription_type && app.plans?.some((plan) => plan.price_inr > 0)
			);
		},
		toggleAllApps() {
			const availableAppNames = new Set(
				this.availableApps.map(this.getAppName)
			);
			if (this.isAllSelected) {
				this.apps = this.apps.filter(
					(app) =>
						app.preinstalled || !availableAppNames.has(this.getAppName(app))
				);
				return;
			}

			const selectedAppNames = new Set(this.apps.map(this.getAppName));
			const appsToAdd = this.availableApps.filter(
				(app) => !selectedAppNames.has(this.getAppName(app))
			);
			this.apps = [
				...this.apps,
				...appsToAdd.filter((app) => !this.requiresPlan(app)),
			];
			this.pendingPlanApps = appsToAdd.filter(this.requiresPlan);
			this.openNextPlanSelector();
		},
		openNextPlanSelector() {
			this.selectedApp = this.pendingPlanApps.shift() || null;
			this.showAppPlanSelectorDialog = Boolean(this.selectedApp);
		},
		selectAppPlan(plan) {
			const selectedAppName = this.getAppName(this.selectedApp);
			this.apps = [
				...this.apps.filter((app) => this.getAppName(app) !== selectedAppName),
				{ ...this.selectedApp, plan },
			];
			this.continuePlanSelection = this.pendingPlanApps.length > 0;
			this.showAppPlanSelectorDialog = false;
		},
		toggleApp(app) {
			if (app.preinstalled) {
				toast.error(app.title + ' is pre-installed and cannot be removed');
			} else if (this.apps.map((a) => a.app).includes(app.app)) {
				this.apps = this.apps.filter((a) => a.app !== app.app);
			} else {
				if (this.requiresPlan(app)) {
					this.selectedApp = app;
					this.showAppPlanSelectorDialog = true;
				} else {
					this.apps = [...this.apps, app];
				}
			}
		},
	},
};
</script>
