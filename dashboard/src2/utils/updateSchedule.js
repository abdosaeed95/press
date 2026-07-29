// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { dayjsCairo, dayjsLocal } from './dayjs';

export const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export const UPDATE_STATUS_STYLES = {
	Scheduled: 'border-blue-200 bg-blue-50 text-blue-700',
	Pending: 'border-amber-200 bg-amber-50 text-amber-700',
	Running: 'border-amber-200 bg-amber-50 text-amber-700',
	Success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
	Failure: 'border-red-200 bg-red-50 text-red-700',
	Fatal: 'border-red-200 bg-red-50 text-red-700',
	Recovering: 'border-violet-200 bg-violet-50 text-violet-700',
	Recovered: 'border-teal-200 bg-teal-50 text-teal-700',
};

export function getCalendarRange(month) {
	const start = dayjsCairo(month).startOf('month').startOf('week');
	return { start, end: start.add(42, 'day') };
}

export function getCalendarDays(month) {
	const current_month = dayjsCairo(month).format('YYYY-MM');
	const { start } = getCalendarRange(month);

	return Array.from({ length: 42 }, (_, index) => {
		const date = start.add(index, 'day');
		return {
			key: date.format('YYYY-MM-DD'),
			date,
			is_current_month: date.format('YYYY-MM') === current_month,
			is_today: date.format('YYYY-MM-DD') === dayjsCairo().format('YYYY-MM-DD'),
			is_weekend: [5, 6].includes(date.day()),
		};
	});
}

export function groupUpdatesByDay(updates) {
	return updates.reduce((days, update) => {
		const day = dayjsLocal(update.event_time).format('YYYY-MM-DD');
		(days[day] ||= []).push(update);
		return days;
	}, {});
}

export function getRescheduledTime(update, day) {
	const time = dayjsLocal(update.scheduled_time || update.event_time).format(
		'HH:mm'
	);
	return dayjsCairo(`${day}T${time}`);
}
