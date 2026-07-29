<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<div class="flex h-full flex-col overflow-hidden bg-gray-50">
		<Header>
			<div class="flex w-full flex-wrap items-center gap-2">
				<Breadcrumbs
					:items="[
						{ label: 'Update Schedule', route: { name: 'Update Schedule' } },
					]"
				/>
				<div class="ml-auto flex items-center gap-2">
					<div class="flex items-center rounded-md border bg-white">
						<Button
							variant="ghost"
							label="Previous month"
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
						<Button variant="ghost" label="Next month" @click="changeMonth(1)">
							<template #icon>
								<i-lucide-chevron-right class="h-4 w-4" />
							</template>
						</Button>
					</div>
					<Button label="Today" @click="goToToday" />
					<Button
						:variant="showPending ? 'solid' : 'subtle'"
						:label="`Pending updates (${pendingSites.length})`"
						@click="showPending = !showPending"
					>
						<template #prefix>
							<i-lucide-panel-right-open class="h-4 w-4" />
						</template>
					</Button>
				</div>
			</div>
		</Header>

		<div class="flex min-h-0 flex-1">
			<main class="min-w-0 flex-1 overflow-auto p-5">
				<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
					<div class="flex flex-wrap gap-2">
						<div class="rounded border bg-white px-3 py-2">
							<div class="text-xs font-medium uppercase text-gray-500">
								Scheduled
							</div>
							<div class="mt-0.5 text-lg font-semibold text-gray-900">
								{{ statusCounts.Scheduled || 0 }}
							</div>
						</div>
						<div class="rounded border bg-white px-3 py-2">
							<div class="text-xs font-medium uppercase text-gray-500">
								Succeeded
							</div>
							<div class="text-emerald-700 mt-0.5 text-lg font-semibold">
								{{ statusCounts.Success || 0 }}
							</div>
						</div>
						<div class="rounded border bg-white px-3 py-2">
							<div class="text-xs font-medium uppercase text-gray-500">
								Failed
							</div>
							<div class="mt-0.5 text-lg font-semibold text-red-700">
								{{ (statusCounts.Failure || 0) + (statusCounts.Fatal || 0) }}
							</div>
						</div>
					</div>
					<div class="flex flex-wrap items-center gap-3 text-xs text-gray-600">
						<span
							v-for="status in legendStatuses"
							:key="status"
							class="flex items-center gap-1.5"
						>
							<span
								class="h-2 w-2 rounded-full"
								:class="statusDotClass(status)"
							/>
							{{ status }}
						</span>
						<Button
							:loading="$resources.schedule.loading"
							label="Refresh"
							@click="loadSchedule"
						>
							<template #prefix>
								<i-lucide-refresh-cw class="h-4 w-4" />
							</template>
						</Button>
					</div>
				</div>

				<ErrorMessage
					v-if="$resources.schedule.error"
					class="mb-4"
					:message="$resources.schedule.error"
				/>

				<div
					class="relative min-w-[840px] overflow-hidden rounded-md border bg-white shadow-sm"
				>
					<div class="grid grid-cols-7 border-b bg-gray-50">
						<div
							v-for="weekday in weekdays"
							:key="weekday"
							class="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500"
							:class="{ 'bg-gray-100 text-gray-600': isWeekendLabel(weekday) }"
						>
							{{ weekday }}
						</div>
					</div>
					<div class="grid grid-cols-7">
						<section
							v-for="day in calendarDays"
							:key="day.key"
							:data-date="day.key"
							:aria-label="day.date.format('dddd, MMMM D, YYYY')"
							class="group relative min-h-[7rem] border-b border-r p-2 transition-colors"
							:class="[
								day.is_current_month ? 'bg-white' : 'bg-gray-50',
								day.is_weekend ? 'bg-gray-50/80' : '',
								dropTarget === day.key
									? 'bg-blue-50 ring-2 ring-inset ring-blue-400'
									: '',
							]"
							@dragenter.prevent="dropTarget = day.key"
							@dragover.prevent
							@dragleave="leaveDay($event, day.key)"
							@drop.prevent="dropOnDay(day)"
						>
							<div class="mb-2 flex items-center justify-between">
								<span
									class="min-w-6 grid h-6 place-items-center rounded-full px-1.5 text-xs font-semibold"
									:class="
										day.is_today
											? 'bg-blue-600 text-white'
											: day.is_current_month
											? 'text-gray-700'
											: 'text-gray-400'
									"
								>
									{{ day.date.date() }}
								</span>
								<span
									v-if="updatesByDay[day.key]?.length"
									class="text-[11px] tabular-nums text-gray-500"
								>
									{{ updatesByDay[day.key].length }}
									{{
										updatesByDay[day.key].length === 1 ? 'update' : 'updates'
									}}
								</span>
							</div>

							<div
								v-if="updatesByDay[day.key]?.length"
								class="mb-2 h-1 overflow-hidden rounded bg-gray-100"
							>
								<div
									class="h-full rounded bg-blue-400"
									:style="{ width: dayLoadWidth(day.key) }"
								/>
							</div>

							<div class="space-y-1.5">
								<article
									v-for="update in updatesByDay[day.key] || []"
									:key="update.name"
									class="rounded border px-2 py-1.5 text-xs shadow-sm transition hover:shadow"
									:class="[
										statusClass(update.status),
										update.status === 'Scheduled'
											? 'cursor-grab active:cursor-grabbing'
											: 'cursor-pointer',
									]"
									:draggable="update.status === 'Scheduled'"
									:aria-label="`${update.site}, ${update.status}, ${eventTime(
										update
									)}`"
									role="button"
									tabindex="0"
									@click="openUpdate(update)"
									@keydown.enter="openUpdate(update)"
									@dragstart.stop="startUpdateDrag(update)"
									@dragend="clearDrag"
								>
									<div class="truncate font-medium" :title="update.site">
										{{ update.site }}
									</div>
									<div class="mt-1 flex items-center gap-1.5 opacity-80">
										<span
											class="h-1.5 w-1.5 rounded-full"
											:class="statusDotClass(update.status)"
										/>
										<span class="truncate">
											{{ update.status }}
											<template v-if="update.update_duration">
												· {{ formatDuration(update.update_duration) }}
											</template>
										</span>
									</div>
									<div
										class="mt-1 text-right text-[10px] tabular-nums opacity-70"
									>
										{{ eventTime(update) }}
									</div>
								</article>
							</div>

							<div
								v-if="draggedItem && !updatesByDay[day.key]?.length"
								class="pointer-events-none absolute inset-x-2 bottom-2 rounded border border-dashed border-blue-300 py-1 text-center text-[11px] text-blue-600 opacity-0 transition group-hover:opacity-100"
							>
								Drop to schedule
							</div>
						</section>
					</div>
					<div
						v-if="$resources.schedule.loading && !scheduleData.updates.length"
						class="absolute inset-0 grid place-items-center bg-white/70"
					>
						<LoadingIndicator class="h-5 w-5" />
					</div>
				</div>
			</main>

			<div
				v-if="showPending && $isMobile"
				class="fixed inset-0 z-20 bg-black/20"
				@click="showPending = false"
			/>
			<aside
				v-if="showPending"
				class="flex min-h-0 w-80 shrink-0 flex-col border-l bg-white"
				:class="{
					'fixed inset-y-0 right-0 z-30 w-[min(90vw,22rem)] shadow-xl':
						$isMobile,
				}"
			>
				<div class="border-b p-4">
					<div class="flex items-start gap-3">
						<div>
							<h2 class="text-base font-semibold text-gray-900">
								Pending updates
							</h2>
							<p class="mt-1 text-xs leading-5 text-gray-500">
								Drag a site onto a day or schedule it with an exact Cairo time.
							</p>
						</div>
						<Button
							class="ml-auto"
							variant="ghost"
							label="Close pending updates"
							@click="showPending = false"
						>
							<template #icon>
								<i-lucide-x class="h-4 w-4" />
							</template>
						</Button>
					</div>
					<TextInput
						v-model="pendingSearch"
						class="mt-3"
						placeholder="Search pending sites"
					>
						<template #prefix>
							<i-lucide-search class="h-4 w-4 text-gray-500" />
						</template>
					</TextInput>
				</div>

				<div class="min-h-0 flex-1 overflow-y-auto p-3">
					<div v-if="filteredPendingSites.length" class="space-y-2">
						<article
							v-for="site in filteredPendingSites"
							:key="site.name"
							:aria-label="`${site.host_name || site.name}, update available`"
							draggable="true"
							class="cursor-grab rounded border bg-white p-3 shadow-sm transition hover:border-blue-300 hover:shadow active:cursor-grabbing"
							@dragstart="startPendingDrag(site)"
							@dragend="clearDrag"
						>
							<div class="flex items-start gap-2">
								<i-lucide-grip-vertical
									class="mt-0.5 h-4 w-4 shrink-0 text-gray-400"
								/>
								<div class="min-w-0 flex-1">
									<div class="truncate text-sm font-medium text-gray-900">
										{{ site.host_name || site.name }}
									</div>
									<div
										class="mt-1 flex items-center gap-1.5 text-xs text-gray-500"
									>
										<span class="h-1.5 w-1.5 rounded-full bg-amber-500" />
										Update available
									</div>
								</div>
								<Button
									label="Schedule"
									variant="subtle"
									@click.stop="openScheduleDialog(site)"
								/>
							</div>
						</article>
					</div>
					<div
						v-else
						class="rounded border border-dashed px-4 py-10 text-center"
					>
						<i-lucide-calendar-check class="mx-auto h-6 w-6 text-gray-400" />
						<div class="mt-2 text-sm font-medium text-gray-700">
							No pending updates
						</div>
						<div class="mt-1 text-xs text-gray-500">
							All available site updates are already scheduled.
						</div>
					</div>
				</div>
			</aside>
		</div>
	</div>
</template>

<script>
import { defineAsyncComponent, h } from 'vue';
import { toast } from 'vue-sonner';
import Header from '../components/Header.vue';
import { renderDialog } from '../utils/components';
import { cairoTimeToServer, dayjsCairo, dayjsLocal } from '../utils/dayjs';
import { getToastErrorMessage } from '../utils/toast';
import {
	getCalendarDays,
	getCalendarRange,
	getRescheduledTime,
	groupUpdatesByDay,
	UPDATE_STATUS_STYLES,
	WEEKDAYS,
} from '../utils/updateSchedule';

export default {
	name: 'UpdateSchedule',
	components: {
		Header,
	},
	data() {
		return {
			month: dayjsCairo().startOf('month'),
			showPending: !this.$isMobile,
			pendingSearch: '',
			draggedItem: null,
			dropTarget: '',
		};
	},
	resources: {
		schedule: {
			url: 'press.api.update_schedule.get',
			initialData: { updates: [], pending_sites: [] },
		},
		runDocMethod: {
			url: 'press.api.client.run_doc_method',
		},
	},
	computed: {
		scheduleData() {
			return (
				this.$resources.schedule.data || {
					updates: [],
					pending_sites: [],
				}
			);
		},
		pendingSites() {
			return this.scheduleData.pending_sites || [];
		},
		filteredPendingSites() {
			const search = this.pendingSearch.trim().toLowerCase();
			if (!search) return this.pendingSites;
			return this.pendingSites.filter((site) =>
				(site.host_name || site.name).toLowerCase().includes(search)
			);
		},
		calendarDays() {
			return getCalendarDays(this.month);
		},
		updatesByDay() {
			return groupUpdatesByDay(this.scheduleData.updates || []);
		},
		statusCounts() {
			return (this.scheduleData.updates || []).reduce((counts, update) => {
				counts[update.status] = (counts[update.status] || 0) + 1;
				return counts;
			}, {});
		},
		maxDailyUpdates() {
			return Math.max(
				1,
				...Object.values(this.updatesByDay).map((updates) => updates.length)
			);
		},
		weekdays() {
			return WEEKDAYS;
		},
		legendStatuses() {
			return ['Scheduled', 'Running', 'Success', 'Failure'];
		},
	},
	mounted() {
		this.loadSchedule();
		this.$socket.emit('doctype_subscribe', 'Site Update');
		this.$socket.on('list_update', this.handleListUpdate);
	},
	beforeUnmount() {
		this.$socket.emit('doctype_unsubscribe', 'Site Update');
		this.$socket.off('list_update', this.handleListUpdate);
	},
	methods: {
		async loadSchedule() {
			const { start, end } = getCalendarRange(this.month);
			await this.$resources.schedule.fetch({
				start: cairoTimeToServer(start.format('YYYY-MM-DDTHH:mm')).format(
					'YYYY-MM-DD HH:mm:ss'
				),
				end: cairoTimeToServer(end.format('YYYY-MM-DDTHH:mm')).format(
					'YYYY-MM-DD HH:mm:ss'
				),
			});
		},
		changeMonth(offset) {
			this.month = this.month.add(offset, 'month').startOf('month');
			this.loadSchedule();
		},
		goToToday() {
			this.month = dayjsCairo().startOf('month');
			this.loadSchedule();
		},
		handleListUpdate(event) {
			if (['Site', 'Site Update'].includes(event.doctype)) {
				this.loadSchedule();
			}
		},
		isWeekendLabel(weekday) {
			return ['Fri', 'Sat'].includes(weekday);
		},
		statusClass(status) {
			return (
				UPDATE_STATUS_STYLES[status] ||
				'border-gray-200 bg-gray-50 text-gray-700'
			);
		},
		statusDotClass(status) {
			return (
				{
					Scheduled: 'bg-blue-500',
					Pending: 'bg-amber-500',
					Running: 'bg-amber-500',
					Success: 'bg-emerald-500',
					Failure: 'bg-red-500',
					Fatal: 'bg-red-500',
					Recovering: 'bg-violet-500',
					Recovered: 'bg-teal-500',
				}[status] || 'bg-gray-500'
			);
		},
		eventTime(update) {
			return dayjsLocal(update.event_time).format('h:mm A');
		},
		formatDuration(duration) {
			const seconds = Math.round(Number(duration));
			if (seconds < 60) return `${seconds}s`;
			return `${Math.floor(seconds / 60)}m`;
		},
		dayLoadWidth(day) {
			return `${Math.max(
				12,
				((this.updatesByDay[day]?.length || 0) / this.maxDailyUpdates) * 100
			)}%`;
		},
		openUpdate(update) {
			this.$router.push({
				name: 'Site Update',
				params: { name: update.site, id: update.name },
			});
		},
		openScheduleDialog(site, initialScheduledTime = '') {
			const scheduledTime =
				initialScheduledTime ||
				dayjsCairo()
					.add(1, 'day')
					.startOf('day')
					.hour(3)
					.format('YYYY-MM-DDTHH:mm');
			const SiteUpdateDialog = defineAsyncComponent(() =>
				import('../components/SiteUpdateDialog.vue')
			);
			renderDialog(
				h(SiteUpdateDialog, {
					site: site.name,
					initialScheduledTime: scheduledTime,
					stayOnPage: true,
					scheduleDays: Math.max(
						7,
						dayjsCairo(scheduledTime)
							.startOf('day')
							.diff(dayjsCairo().startOf('day'), 'day') + 1
					),
					onScheduled: this.loadSchedule,
				})
			);
		},
		startPendingDrag(site) {
			this.draggedItem = { type: 'pending', site };
		},
		startUpdateDrag(update) {
			this.draggedItem = { type: 'scheduled', update };
		},
		clearDrag() {
			this.draggedItem = null;
			this.dropTarget = '';
		},
		leaveDay(event, day) {
			if (!event.currentTarget.contains(event.relatedTarget)) {
				if (this.dropTarget === day) this.dropTarget = '';
			}
		},
		dropOnDay(day) {
			const draggedItem = this.draggedItem;
			this.clearDrag();
			if (!draggedItem) return;

			if (draggedItem.type === 'pending') {
				const scheduledTime = this.defaultScheduleTime(day.date);
				if (!scheduledTime) return;
				this.openScheduleDialog(
					draggedItem.site,
					scheduledTime.format('YYYY-MM-DDTHH:mm')
				);
				return;
			}

			this.rescheduleUpdate(draggedItem.update, day.key);
		},
		defaultScheduleTime(day) {
			const now = dayjsCairo();
			let scheduledTime = day.hour(3).minute(0).second(0);
			if (scheduledTime.isAfter(now)) return scheduledTime;

			if (day.format('YYYY-MM-DD') !== now.format('YYYY-MM-DD')) {
				toast.error('Updates cannot be scheduled in the past.');
				return;
			}

			const minutes = Math.ceil((now.minute() + 1) / 15) * 15;
			return now.minute(0).second(0).add(minutes, 'minute');
		},
		rescheduleUpdate(update, day) {
			const scheduledTime = getRescheduledTime(update, day);
			if (!scheduledTime.isAfter(dayjsCairo())) {
				toast.error('Updates cannot be rescheduled in the past.');
				return;
			}

			const promise = this.$resources.runDocMethod.submit({
				dt: 'Site',
				dn: update.site,
				method: 'edit_scheduled_update',
				args: {
					name: update.name,
					skip_failing_patches: Boolean(update.skipped_failing_patches),
					skip_backups: Boolean(update.skipped_backups),
					scheduled_time: cairoTimeToServer(
						scheduledTime.format('YYYY-MM-DDTHH:mm')
					).format('YYYY-MM-DDTHH:mm'),
				},
			});

			toast.promise(promise, {
				loading: `Rescheduling ${update.site}...`,
				success: () => {
					this.loadSchedule();
					return `${update.site} rescheduled to ${scheduledTime.format(
						'ddd, MMM D [at] h:mm A'
					)}`;
				},
				error: (error) => getToastErrorMessage(error),
			});
		},
	},
};
</script>
