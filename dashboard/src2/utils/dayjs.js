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

const CAIRO_TIMEZONE = 'Africa/Cairo';
const SERVER_TIMEZONE = 'Asia/Calcutta';

export function dayjsLocal(dateTimeString) {
	const dateTime = dateTimeString
		? dayjs.tz(dateTimeString, SERVER_TIMEZONE)
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
		'h:mm A',
	)}`;
}

export function cairoTimeToServer(dateTimeString) {
	return dayjsCairo(dateTimeString).tz(SERVER_TIMEZONE);
}

export default dayjs;
