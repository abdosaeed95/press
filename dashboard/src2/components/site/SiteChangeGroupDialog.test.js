// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import SiteChangeGroupDialog from './SiteChangeGroupDialog.vue';

describe('Site change group dialog', () => {
	it('places the skip migrate option after destination app installation', () => {
		const source = readFileSync(
			new URL('./SiteChangeGroupDialog.vue', import.meta.url),
			'utf8',
		);

		expect(
			source.indexOf('Install all apps from the destination Bench Group'),
		).toBeLessThan(source.indexOf('Skip migrate command'));
		expect(source).toContain('skip_migrate: skipMigrate');
		expect(SiteChangeGroupDialog.data().skipMigrate).toBe(false);
	});

	it('supports immediate and scheduled bench changes', () => {
		const source = readFileSync(
			new URL('./SiteChangeGroupDialog.vue', import.meta.url),
			'utf8',
		);

		expect(source).toContain('DateTimeControl');
		expect(source).toContain('scheduled_datetime: datetimeInServerTimezone');
		expect(source).toContain(
			"targetDateTime ? `at ${targetDateTimeInCairo}` : 'Now'",
		);
		expect(SiteChangeGroupDialog.data().targetDateTime).toBeNull();
	});
});
