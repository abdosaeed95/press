// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import dayjs from 'dayjs/esm';
import relativeTime from 'dayjs/esm/plugin/relativeTime';
import localizedFormat from 'dayjs/esm/plugin/localizedFormat';
import updateLocale from 'dayjs/esm/plugin/updateLocale';
import isToday from 'dayjs/esm/plugin/isToday';
import duration from 'dayjs/esm/plugin/duration';
import utc from 'dayjs/esm/plugin/utc';
import timezone from 'dayjs/esm/plugin/timezone';
import advancedFormat from 'dayjs/plugin/advancedFormat';

dayjs.extend(updateLocale);
dayjs.extend(relativeTime);
dayjs.extend(localizedFormat);
dayjs.extend(isToday);
dayjs.extend(duration);
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(advancedFormat);

export const CAIRO_TIMEZONE = 'Africa/Cairo';
const STORED_DATETIME_TIMEZONE = 'Asia/Calcutta';

export function dayjsLocal(dateTimeString) {
	const dateTime = dateTimeString
		? dayjs.tz(dateTimeString, STORED_DATETIME_TIMEZONE)
		: dayjs();
	return dateTime.tz(CAIRO_TIMEZONE);
}

export function dayjsCairo(dateTimeString) {
	return dateTimeString
		? dayjs.tz(dateTimeString, CAIRO_TIMEZONE)
		: dayjs().tz(CAIRO_TIMEZONE);
}

export function scheduledTimeLabel(dateTimeString) {
	const scheduledTime = dayjsLocal(dateTimeString);
	const days = scheduledTime
		.startOf('day')
		.diff(dayjsLocal().startOf('day'), 'day');
	const day =
		days === 0
			? 'Today'
			: days === 1
			? 'Tomorrow'
			: days > 1 && days < 14
			? `Next ${scheduledTime.format('ddd')}`
			: scheduledTime.format('ddd');

	return `${day}, ${scheduledTime.format('MMM D')} at ${scheduledTime.format(
		'h:mm A'
	)}`;
}

export function cairoTimeToServer(dateTimeString) {
	return dayjsCairo(dateTimeString).tz(STORED_DATETIME_TIMEZONE);
}

export function distributeSiteUpdateTimes(
	sites,
	distributionDays = 1,
	minimumTime = null
) {
	let firstDay = dayjsCairo().add(1, 'day').startOf('day');
	const minimum = minimumTime ? dayjsCairo(minimumTime) : null;
	if (minimum?.startOf('day').isAfter(firstDay)) {
		firstDay = minimum.startOf('day');
	}

	const isBlockedDay = (day) =>
		[5, 6].includes(day.day()) ||
		day.date() <= 3 ||
		day.date() === day.daysInMonth();
	const nextSchedulingDay = (day) => {
		while (isBlockedDay(day)) {
			day = day.add(1, 'day');
		}
		return day;
	};
	firstDay = nextSchedulingDay(firstDay);

	const generateTimes = () => {
		const days = Array.from({ length: distributionDays }, (_, index) =>
			firstDay.add(index, 'day')
		).filter((day) => !isBlockedDay(day));

		return sites.map((_, index) => {
			const offset =
				Math.floor(((index + 0.5) * days.length * 12) / sites.length) * 15;
			return days[Math.floor(offset / 180)]
				.hour(3)
				.minute(offset % 180)
				.format('YYYY-MM-DDTHH:mm');
		});
	};

	let times = generateTimes();
	if (minimum && !dayjsCairo(times[0]).isAfter(minimum)) {
		firstDay = nextSchedulingDay(firstDay.add(1, 'day'));
		times = generateTimes();
	}

	return Object.fromEntries(
		sites.map((site, index) => [
			site.name,
			{ updateTime: 'scheduled', scheduledTime: times[index] },
		])
	);
}

export default dayjs;
