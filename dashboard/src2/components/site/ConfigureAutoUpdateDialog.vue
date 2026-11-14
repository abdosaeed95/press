<template>
	<Dialog v-model="show" :options="{ title: 'Configure Auto Update' }">
		<template #body-content>
			<div class="mt-8 space-y-4">
				<Switch
					v-model="enableAutoUpdate"
					label="Enable Auto Update"
					description="Automatically schedule site updates whenever available"
					:disabled="$site.setValue.loading"
				/>
				<form id="auto-update-testing-age" @submit.prevent="saveTestingAge">
					<FormControl
						v-model="minimumTestingDays"
						type="number"
						min="0"
						max="2147483647"
						step="1"
						required
						label="Minimum testing age (days)"
						description="Each changed app release must run on another site on your team for this many full days. Use 0 to turn off the requirement."
						:disabled="$site.setValue.loading"
					/>
				</form>
				<ErrorMessage :message="$site.setValue.error" />
			</div>
		</template>
		<template #actions>
			<Button
				type="submit"
				form="auto-update-testing-age"
				label="Save"
				variant="solid"
				:loading="$site.setValue.loading"
			/>
		</template>
	</Dialog>
</template>

<script>
import { Switch, getCachedDocumentResource } from 'frappe-ui';

export default {
	props: {
		site: {
			type: String,
			required: true,
		},
	},
	components: { Switch },
	data() {
		return {
			show: true,
			minimumTestingDays:
				getCachedDocumentResource('Site', this.site).doc.minimum_testing_days ??
				0,
		};
	},
	computed: {
		$site() {
			return getCachedDocumentResource('Site', this.site);
		},
		enableAutoUpdate: {
			get() {
				return !this.$site?.doc.skip_auto_updates;
			},
			set(value) {
				this.$site.setValue
					.submit({ skip_auto_updates: !value })
					.catch(() => {});
			},
		},
	},
	methods: {
		async saveTestingAge() {
			try {
				await this.$site.setValue.submit({
					minimum_testing_days: Number(this.minimumTestingDays),
				});
				this.show = false;
			} catch {
				// The resource exposes the error in the dialog.
			}
		},
	},
};
</script>
