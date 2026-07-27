// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
import ActionButton from './ActionButton.vue';

describe('ActionButton dropdown', () => {
	it('shows a requested dropdown button label', () => {
		const props = ActionButton.computed.dropdownProps.call({
			$attrs: {
				label: 'Bulk Actions',
				options: [],
				showLabel: true,
			},
		});

		expect(props.button.label).toBe('Bulk Actions');
		expect(props.button.slots).toEqual({});
	});

	it('keeps the compact options button by default', () => {
		const props = ActionButton.computed.dropdownProps.call({
			$attrs: { label: 'Actions', options: [] },
		});

		expect(props.button.label).toBe('Options');
		expect(props.button.slots.icon).toBeTruthy();
	});
});
