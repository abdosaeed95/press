// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
import { utils } from '../../src/utils';
import ServerCharts from '../components/server/ServerCharts.vue';
import ServerLoadAverage from '../components/server/ServerLoadAverage.vue';
import SiteDailyUsage from '../components/SiteDailyUsage.vue';
import SiteAnalytics from '../components/site/SiteAnalytics.vue';
import SiteRequestLogs from '../components/site/performance/SiteRequestLogs.vue';
import { CAIRO_TIMEZONE } from './dayjs';

describe('Cairo cloud timezone', () => {
	it('formats stored cloud dates in Cairo', () => {
		expect(
			utils.methods.$date('2026-07-28 21:30:00').toFormat('yyyy-MM-dd HH:mm')
		).toBe('2026-07-28 19:00');
	});

	it('uses Cairo for site analytics requests', () => {
		const daily_usage = SiteDailyUsage.resources.requestCounter.call({
			site: 'site.example.com',
		});
		const analytics = SiteAnalytics.data.call({});
		const request_logs = SiteRequestLogs.computed.requestLogsOptions.call({
			name: 'site.example.com',
			start: 0,
			today: '2026-07-28',
			$isMobile: false,
		});

		expect(daily_usage.params.timezone).toBe(CAIRO_TIMEZONE);
		expect(analytics.timezone).toBe(CAIRO_TIMEZONE);
		expect(request_logs.resource().makeParams().timezone).toBe(CAIRO_TIMEZONE);
	});

	it('uses Cairo for server analytics requests', () => {
		const load_average = ServerLoadAverage.resources.loadavg.call({
			server: 'server.example.com',
		});
		const server_charts = ServerCharts.data.call({
			$route: { query: {} },
			$theme: {
				colors: new Proxy({}, { get: () => ({ 500: '#000000' }) }),
			},
			serverName: 'server.example.com',
		});

		expect(load_average.params.timezone).toBe(CAIRO_TIMEZONE);
		expect(server_charts.timezone).toBe(CAIRO_TIMEZONE);
	});
});
