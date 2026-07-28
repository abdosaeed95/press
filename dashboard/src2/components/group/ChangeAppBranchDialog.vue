<template>
	<Dialog
		v-model="showDialog"
		:options="{ title: `Change branch for ${app.title}` }"
	>
		<template #body-content>
			<div class="flex flex-col items-center">
				<LoadingText class="my-4" v-if="$resources.branches.loading" />
				<FormControl
					v-else
					class="w-full"
					label="Select Branch"
					type="select"
					:options="branchOptions"
					v-model="selectedBranch"
				/>
				<ReleaseUsage
					v-if="selectedRelease"
					class="mt-3 w-full"
					:release="selectedRelease.name"
					:usage="selectedRelease.usage"
				/>
				<ErrorMessage
					class="mt-2 w-full"
					:message="$resources.changeBranch.error"
				/>
			</div>
		</template>
		<template #actions>
			<Button
				v-if="!$resources.branches.loading"
				class="w-full"
				variant="solid"
				label="Change Branch"
				:loading="$resources.changeBranch.loading"
				@click="changeBranch()"
			/>
		</template>
	</Dialog>
</template>

<script>
import { DashboardError } from '../../utils/error';
import ReleaseUsage from './ReleaseUsage.vue';

export default {
	name: 'ChangeAppBranchDialog',
	components: { ReleaseUsage },
	emits: ['branchChange'],
	props: ['bench', 'app'],
	data() {
		return {
			selectedBranch: this.app.branch,
			showDialog: true,
		};
	},
	resources: {
		branches() {
			return {
				url: 'press.api.bench.branch_list',
				params: {
					name: this.bench,
					app: this.app.name,
				},
				auto: true,
				initialData: [],
			};
		},
		changeBranch() {
			return {
				url: 'press.api.bench.change_branch',
				onSuccess() {
					this.$emit('branchChange');
					this.showDialog = false;
				},
				validate() {
					if (this.selectedBranch == this.app.branch) {
						throw new DashboardError('Please select a different branch');
					}
				},
			};
		},
	},
	computed: {
		branchOptions() {
			return this.$resources.branches.data.map((branch) => branch.name);
		},
		selectedRelease() {
			return this.$resources.branches.data.find(
				(branch) => branch.name === this.selectedBranch,
			)?.release;
		},
	},
	methods: {
		changeBranch() {
			this.$resources.changeBranch.submit({
				name: this.bench,
				app: this.app.name,
				to_branch: this.selectedBranch,
			});
		},
	},
};
</script>
