// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
import ReleaseUsage from './ReleaseUsage.vue';

describe('ReleaseUsage', () => {
	it('shows how long the selected release has run in the current team', () => {
		expect(
			ReleaseUsage.computed.testedLabel.call({
				usage: { tested_days: 4 },
			})
		).toBe('Tested for 4 days');
	});

	it('uses singular wording for one day', () => {
		expect(
			ReleaseUsage.computed.testedLabel.call({
				usage: { tested_days: 1 },
			})
		).toBe('Tested for 1 day');
	});
});
