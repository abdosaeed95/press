<template>
	<Dialog
		v-model="show"
		:options="{
			title: 'Install app on your site',
			size: '4xl',
		}"
	>
		<template #body-content>
			<ObjectList :options="listOptions" />
		</template>
	</Dialog>
</template>

<script>
import { FormControl, getCachedDocumentResource } from 'frappe-ui';
import { h } from 'vue';
import { toast } from 'vue-sonner';
import router from '../../router';
import ObjectList from '../ObjectList.vue';
import { getToastErrorMessage } from '../../utils/toast';

export default {
	props: {
		site: {
			type: String,
			required: true,
		},
	},
	emits: ['installed'],
	components: {
		ObjectList,
	},
	resources: {
		installApps() {
			return {
				url: 'press.api.client.run_doc_method',
				makeParams: (args) => ({
					dt: 'Site',
					dn: this.site,
					method: 'install_apps',
					args,
				}),
			};
		},
	},
	data() {
		return {
			show: true,
			selectedPlans: {},
		};
	},
	computed: {
		$site() {
			return getCachedDocumentResource('Site', this.site);
		},
		listOptions() {
			return {
				label: 'App',
				fieldname: 'app',
				fieldtype: 'ListSelection',
				selectable: true,
				emptyStateMessage:
					'No apps found' +
					(!this.$site.doc?.group_public
						? '. Please add them from your bench.'
						: ''),
				columns: [
					{
						label: 'Title',
						fieldname: 'title',
						class: 'font-medium',
						width: 2,
						format: (value, row) => value || row.app_title,
					},
					{
						label: 'Repo',
						fieldname: 'repository_owner',
						class: 'text-gray-600',
						width: '10rem',
					},
					{
						label: 'Branch',
						fieldname: 'branch',
						class: 'text-gray-600',
						width: '10rem',
					},
					{
						label: 'Plan',
						fieldname: 'plans',
						width: '12rem',
						type: 'Component',
						component: ({ row }) => {
							if (!this.requiresPlan(row)) return h('span', '—');
							return h(FormControl, {
								type: 'select',
								placeholder: 'Select plan',
								options: row.plans.map((plan) => ({
									label: plan.title,
									value: plan.name,
								})),
								modelValue: this.selectedPlans[row.app],
								'onUpdate:modelValue': (plan) => {
									this.selectedPlans[row.app] = plan;
								},
							});
						},
					},
					{
						label: '',
						fieldname: '',
						align: 'right',
						type: 'Button',
						width: '5rem',
						Button: ({ row }) => {
							return {
								label: 'Install',
								disabled:
									this.requiresPlan(row) && !this.selectedPlans[row.app],
								onClick: () => {
									this.installRows([row]);
								},
							};
						},
					},
				],
				primaryAction: ({ selectedRows }) => {
					const missingPlan = selectedRows.some(
						(row) => this.requiresPlan(row) && !this.selectedPlans[row.app]
					);
					return {
						label: selectedRows.length
							? `Install ${selectedRows.length} Apps`
							: 'Install Apps',
						variant: 'solid',
						loading: this.$resources.installApps.loading,
						disabled: !selectedRows.length || missingPlan,
						onClick: () => this.installRows(selectedRows),
					};
				},
				resource: () => {
					return {
						url: 'press.api.site.available_apps',
						params: {
							name: this.site,
						},
						auto: true,
					};
				},
			};
		},
	},
	methods: {
		requiresPlan(row) {
			return (
				row.plans?.some((plan) => plan.price_inr > 0) &&
				row.team !== this.$site.doc?.team
			);
		},
		installRows(rows) {
			if (this.$resources.installApps.loading) return;

			toast.promise(
				this.$resources.installApps.submit({
					apps: rows.map((row) => ({
						app: row.app,
						plan: this.selectedPlans[row.app],
					})),
				}),
				{
					loading: 'Queueing app installations...',
					success: () => {
						router.push({
							name: 'Site Jobs',
							params: { name: this.site },
						});
						this.$emit('installed');
						this.show = false;
						return 'Apps will be installed one by one';
					},
					error: (e) => getToastErrorMessage(e),
				}
			);
		},
	},
};
</script>
