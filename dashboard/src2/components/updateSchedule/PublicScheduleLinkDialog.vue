<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<Dialog
		v-model="show"
		:options="{ title: 'Share Update Schedule', size: 'xl' }"
	>
		<template #body-content>
			<div class="space-y-5">
				<div class="rounded-md border bg-gray-50 p-4">
					<div class="text-sm font-medium text-gray-900">
						Create public link
					</div>
					<p class="mt-1 text-sm text-gray-600">
						Anyone with the link and password can view this team's update
						schedule. Public links never allow changes.
					</p>
					<div class="mt-3 flex items-end gap-2">
						<FormControl
							v-model="title"
							class="min-w-0 flex-1"
							label="Link title"
							placeholder="Update Schedule"
						/>
						<Button
							:disabled="!title.trim()"
							:loading="$resources.createLink.loading"
							label="Create link"
							variant="solid"
							@click="createLink"
						/>
					</div>
				</div>

				<div
					v-if="credentials"
					class="rounded-md border border-emerald-200 bg-emerald-50 p-4"
				>
					<div class="font-medium text-emerald-900">
						Copy these credentials now
					</div>
					<p class="mt-1 text-sm text-emerald-800">
						The password will not be shown again.
					</p>
					<div class="mt-3 space-y-3">
						<ClickToCopyField :text-content="credentials.url" />
						<ClickToCopyField :text-content="credentials.password" />
						<Button
							label="Copy link and password"
							variant="subtle"
							@click="copyCredentials"
						/>
					</div>
				</div>

				<div
					v-if="editingLink"
					class="rounded-md border border-blue-200 bg-blue-50 p-4"
				>
					<div class="font-medium text-blue-900">
						Change password for {{ editingLink.title }}
					</div>
					<p class="mt-1 text-sm text-blue-800">
						Leave the field empty to generate a new secure password.
					</p>
					<FormControl
						v-model="newPassword"
						class="mt-3"
						label="New password"
						type="password"
					/>
					<div class="mt-3 flex gap-2">
						<Button
							:loading="$resources.changePassword.loading"
							label="Change password"
							variant="solid"
							@click="changePassword"
						/>
						<Button
							label="Cancel"
							variant="ghost"
							@click="editingLink = null"
						/>
					</div>
				</div>

				<div>
					<div class="mb-2 flex items-center justify-between">
						<div class="text-sm font-medium text-gray-900">Existing links</div>
						<Button
							:loading="$resources.links.loading"
							label="Refresh"
							variant="ghost"
							@click="$resources.links.fetch()"
						/>
					</div>
					<ErrorMessage :message="$resources.links.error" />
					<div
						v-if="$resources.links.data.length"
						class="divide-y rounded-md border"
					>
						<div
							v-for="link in $resources.links.data"
							:key="link.name"
							class="p-4"
						>
							<div class="flex flex-wrap items-start gap-3">
								<div class="min-w-0 flex-1">
									<div class="flex items-center gap-2">
										<span class="truncate text-sm font-medium text-gray-900">
											{{ link.title }}
										</span>
										<Badge
											:label="link.enabled ? 'Active' : 'Disabled'"
											:theme="link.enabled ? 'green' : 'gray'"
										/>
									</div>
									<div class="mt-2">
										<ClickToCopyField :text-content="publicUrl(link.token)" />
									</div>
								</div>
								<div class="flex flex-wrap gap-2">
									<Button
										label="Change password"
										variant="subtle"
										@click="selectPasswordLink(link)"
									/>
									<Button
										:label="link.enabled ? 'Disable' : 'Enable'"
										:variant="link.enabled ? 'subtle' : 'solid'"
										@click="setEnabled(link)"
									/>
								</div>
							</div>
						</div>
					</div>
					<div
						v-else-if="!$resources.links.loading"
						class="rounded-md border border-dashed p-8 text-center text-sm text-gray-500"
					>
						No public links have been created.
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script>
import { toast } from 'vue-sonner';
import ClickToCopyField from '../ClickToCopyField.vue';
import { getToastErrorMessage } from '../../utils/toast';

export default {
	name: 'PublicScheduleLinkDialog',
	components: { ClickToCopyField },
	data() {
		return {
			show: true,
			title: 'Update Schedule',
			credentials: null,
			editingLink: null,
			newPassword: '',
		};
	},
	resources: {
		links: {
			url: 'press.api.public_update_schedule.get_links',
			initialData: [],
			auto: true,
		},
		createLink: {
			url: 'press.api.public_update_schedule.create_link',
		},
		changePassword: {
			url: 'press.api.public_update_schedule.change_password',
		},
		setEnabled: {
			url: 'press.api.public_update_schedule.set_enabled',
		},
	},
	methods: {
		async createLink() {
			try {
				const link = await this.$resources.createLink.submit({
					title: this.title.trim(),
				});
				this.credentials = {
					url: this.publicUrl(link.token),
					password: link.password,
				};
				await this.$resources.links.fetch();
				toast.success('Public schedule link created.');
			} catch (error) {
				toast.error(getToastErrorMessage(error));
			}
		},
		selectPasswordLink(link) {
			this.editingLink = link;
			this.newPassword = '';
			this.credentials = null;
		},
		async changePassword() {
			try {
				const result = await this.$resources.changePassword.submit({
					name: this.editingLink.name,
					password: this.newPassword,
				});
				this.credentials = {
					url: this.publicUrl(this.editingLink.token),
					password: result.password,
				};
				this.editingLink = null;
				await this.$resources.links.fetch();
				toast.success('Public link password changed.');
			} catch (error) {
				toast.error(getToastErrorMessage(error));
			}
		},
		async setEnabled(link) {
			try {
				await this.$resources.setEnabled.submit({
					name: link.name,
					enabled: Number(!link.enabled),
				});
				await this.$resources.links.fetch();
				toast.success(`Public link ${link.enabled ? 'disabled' : 'enabled'}.`);
			} catch (error) {
				toast.error(getToastErrorMessage(error));
			}
		},
		publicUrl(token) {
			return `${window.location.origin}/dashboard/public/update-schedule/${token}`;
		},
		async copyCredentials() {
			await navigator.clipboard.writeText(
				`${this.credentials.url}\nPassword: ${this.credentials.password}`,
			);
			toast.success('Link and password copied.');
		},
	},
};
</script>
