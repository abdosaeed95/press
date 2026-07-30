<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<div class="min-h-full bg-gray-50">
		<LoginBox
			v-if="!accessToken"
			title="Update Schedule"
			subtitle="Enter the password supplied with this public link."
		>
			<form @submit.prevent="unlock">
				<FormControl
					v-model="password"
					autocomplete="current-password"
					label="Password"
					type="password"
				/>
				<Button
					class="mt-4 w-full"
					:disabled="!password"
					:loading="$resources.unlock.loading"
					label="View schedule"
					variant="solid"
				/>
				<ErrorMessage class="mt-3" :message="$resources.unlock.error" />
			</form>
		</LoginBox>

		<template v-else>
			<header class="border-b bg-white">
				<div
					class="mx-auto flex max-w-screen-2xl flex-wrap items-center gap-3 px-4 py-4 sm:px-6"
				>
					<div>
						<div class="flex items-center gap-2">
							<h1 class="text-lg font-semibold text-gray-900">{{ title }}</h1>
							<Badge label="Read only" theme="blue" />
						</div>
						<p class="mt-1 text-xs text-gray-500">
							Last refreshed {{ formattedRefreshTime }}
						</p>
					</div>
					<div class="ml-auto flex flex-wrap items-center gap-2">
						<div class="flex items-center rounded-md border bg-white">
							<Button
								label="Previous month"
								variant="ghost"
								@click="changeMonth(-1)"
							>
								<template #icon>
									<i-lucide-chevron-left class="h-4 w-4" />
								</template>
							</Button>
							<div
								class="min-w-36 px-2 text-center text-sm font-medium text-gray-800"
							>
								{{ month.format('MMMM YYYY') }}
							</div>
							<Button
								label="Next month"
								variant="ghost"
								@click="changeMonth(1)"
							>
								<template #icon>
									<i-lucide-chevron-right class="h-4 w-4" />
								</template>
							</Button>
						</div>
						<Button label="Today" @click="goToToday" />
						<Button
							:loading="$resources.schedule.loading"
							label="Refresh"
							@click="loadSchedule"
						/>
						<Button label="Lock" variant="ghost" @click="lock" />
					</div>
				</div>
			</header>

			<main class="mx-auto max-w-screen-2xl p-4 sm:p-6">
				<div class="mb-4 flex flex-wrap gap-2">
					<div
						v-for="status in summaryStatuses"
						:key="status.label"
						class="rounded border bg-white px-3 py-2"
					>
						<div class="text-xs font-medium uppercase text-gray-500">
							{{ status.label }}
						</div>
						<div class="mt-0.5 text-lg font-semibold" :class="status.class">
							{{ status.count }}
						</div>
					</div>
				</div>
				<ErrorMessage class="mb-4" :message="$resources.schedule.error" />
				<div class="overflow-x-auto">
					<PublicScheduleCalendar
						:month="month"
						:updates="scheduleData.updates"
					/>
				</div>
			</main>
		</template>
	</div>
</template>

<script>
import LoginBox from '../components/auth/LoginBox.vue';
import PublicScheduleCalendar from '../components/updateSchedule/PublicScheduleCalendar.vue';
import { cairoTimeToServer, dayjsCairo, dayjsLocal } from '../utils/dayjs';
import { getCalendarRange } from '../utils/updateSchedule';

const storageKey = (token) => `press-public-update-schedule-v1:${token}`;

function getStoredAccessToken(token) {
	try {
		return sessionStorage.getItem(storageKey(token)) || '';
	} catch {
		return '';
	}
}

export default {
	name: 'PublicUpdateSchedule',
	components: { LoginBox, PublicScheduleCalendar },
	props: {
		token: { type: String, required: true },
	},
	data() {
		return {
			accessToken: getStoredAccessToken(this.token),
			password: '',
			title: 'Update Schedule',
			month: dayjsCairo().startOf('month'),
		};
	},
	resources: {
		unlock: {
			url: 'press.api.public_update_schedule.unlock',
		},
		schedule: {
			url: 'press.api.public_update_schedule.get_public_schedule',
			initialData: { updates: [], last_refreshed: '' },
		},
	},
	computed: {
		scheduleData() {
			return (
				this.$resources.schedule.data || {
					updates: [],
					last_refreshed: '',
				}
			);
		},
		formattedRefreshTime() {
			if (!this.scheduleData.last_refreshed) return 'not yet';
			return dayjsLocal(this.scheduleData.last_refreshed).format(
				'ddd, MMM D [at] h:mm A',
			);
		},
		summaryStatuses() {
			const counts = this.scheduleData.updates.reduce((result, update) => {
				result[update.status] = (result[update.status] || 0) + 1;
				return result;
			}, {});
			return [
				{
					label: 'Scheduled',
					count: counts.Scheduled || 0,
					class: 'text-blue-700',
				},
				{
					label: 'Succeeded',
					count: counts.Success || 0,
					class: 'text-emerald-700',
				},
				{
					label: 'Failed',
					count: (counts.Failure || 0) + (counts.Fatal || 0),
					class: 'text-red-700',
				},
			];
		},
	},
	mounted() {
		if (this.accessToken) this.loadSchedule();
	},
	methods: {
		async unlock() {
			try {
				const result = await this.$resources.unlock.submit({
					token: this.token,
					password: this.password,
				});
				this.accessToken = result.access_token;
				this.title = result.title;
				this.password = '';
				this.storeAccessToken();
				await this.loadSchedule();
			} catch {
				// The resource displays the server's authentication error.
			}
		},
		async loadSchedule() {
			const { start, end } = getCalendarRange(this.month);
			try {
				const result = await this.$resources.schedule.submit({
					token: this.token,
					access_token: this.accessToken,
					start: cairoTimeToServer(start.format('YYYY-MM-DDTHH:mm')).format(
						'YYYY-MM-DD HH:mm:ss',
					),
					end: cairoTimeToServer(end.format('YYYY-MM-DDTHH:mm')).format(
						'YYYY-MM-DD HH:mm:ss',
					),
				});
				this.title = result.title;
			} catch (error) {
				if (error.exc_type === 'AuthenticationError') this.lock();
			}
		},
		changeMonth(offset) {
			this.month = this.month.add(offset, 'month').startOf('month');
			this.loadSchedule();
		},
		goToToday() {
			this.month = dayjsCairo().startOf('month');
			this.loadSchedule();
		},
		lock() {
			this.accessToken = '';
			this.$resources.schedule.reset();
			try {
				sessionStorage.removeItem(storageKey(this.token));
			} catch {
				// Browser storage can be unavailable in private browsing.
			}
		},
		storeAccessToken() {
			try {
				sessionStorage.setItem(storageKey(this.token), this.accessToken);
			} catch {
				// The link remains usable for the current page session.
			}
		},
	},
};
</script>
