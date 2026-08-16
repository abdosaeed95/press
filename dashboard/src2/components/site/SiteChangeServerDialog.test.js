// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import SiteChangeServerDialog from './SiteChangeServerDialog.vue';

describe('Site change server dialog', () => {
	it('shows whether the server change is immediate or scheduled', () => {
		const source = readFileSync(
			new URL('./SiteChangeServerDialog.vue', import.meta.url),
			'utf8'
		);

		expect(source).toContain('DateTimeControl');
		expect(source).toContain('scheduled_datetime: datetimeInServerTimezone');
		expect(source).toContain(
			"targetDateTime ? `at ${targetDateTimeInCairo}` : 'Now'"
		);
		expect(SiteChangeServerDialog.data().targetDateTime).toBeNull();
	});
});
