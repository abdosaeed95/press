<!-- Copyright (c) 2026, Frappe and contributors -->
<!-- For license information, please see license.txt -->

<template>
	<div
		class="min-w-[840px] overflow-hidden rounded-md border bg-white shadow-sm"
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
				:aria-label="day.date.format('dddd, MMMM D, YYYY')"
				class="min-h-[7rem] border-b border-r p-2"
				:class="[
					day.is_current_month ? 'bg-white' : 'bg-gray-50',
					day.is_weekend ? 'bg-gray-50/80' : '',
				]"
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
						{{ updatesByDay[day.key].length === 1 ? 'update' : 'updates' }}
					</span>
				</div>

				<div class="space-y-1.5">
					<article
						v-for="update in updatesByDay[day.key] || []"
						:key="`${update.site}-${update.event_time}`"
						class="rounded border px-2 py-1.5 text-xs shadow-sm"
						:class="statusClass(update.status)"
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
						<div class="mt-1 text-right text-[10px] tabular-nums opacity-70">
							{{ eventTime(update) }}
						</div>
					</article>
				</div>
			</section>
		</div>
	</div>
</template>

<script>
import { dayjsLocal } from '../../utils/dayjs';
import {
	getCalendarDays,
	groupUpdatesByDay,
	UPDATE_STATUS_STYLES,
	WEEKDAYS,
} from '../../utils/updateSchedule';

export default {
	name: 'PublicScheduleCalendar',
	props: {
		month: { type: Object, required: true },
		updates: { type: Array, default: () => [] },
	},
	computed: {
		calendarDays() {
			return getCalendarDays(this.month);
		},
		updatesByDay() {
			return groupUpdatesByDay(this.updates);
		},
		weekdays() {
			return WEEKDAYS;
		},
	},
	methods: {
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
	},
};
</script>
